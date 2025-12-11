"""
Step 1: Extract and Store Content in Sheets (NO SCORING)
This step extracts structured data from ALREADY SCRAPED DATA in Raw_Scraped_Data sheet
and stores extracted content in Content_Extraction sheet for verification before scoring.

NOTE: This does NOT call any APIs - it reads from scraped data already stored in sheets.
"""

import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from src.sheets_manager import SheetsManager
from src.rule_based_extractor import RuleBasedExtractor
from src.utils.logger import setup_logger

logger = setup_logger("ExtractionStep1")


class ContentExtractor:
    """Extract and store content in sheets without scoring"""
    
    def __init__(self):
        self.sheets = SheetsManager()
        self.rule_extractor = RuleBasedExtractor()
        logger.info("✅ Content Extractor initialized")
    
    def extract_property_content(self, property_id: str) -> bool:
        """
        Extract content for a single property and store in sheets
        
        Args:
            property_id: Property ID (e.g., 'P001')
            
        Returns:
            Success status
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Extracting Content for Property: {property_id}")
        logger.info(f"{'='*80}")
        
        try:
            # Get scraped data
            raw_df = self.sheets.read_sheet('Raw_Scraped_Data')
            property_data = raw_df[raw_df['Property_ID'] == property_id]
            
            if len(property_data) != 2:
                logger.error(f"Expected 2 rows (Amber + Uhomes), found {len(property_data)}")
                return False
            
            # Extract Amber content
            amber_row = property_data[property_data['Platform'] == 'amber'].iloc[0]
            amber_success = self._extract_platform_content(property_id, amber_row, 'amber')
            
            # Extract UHomes content
            uhomes_row = property_data[property_data['Platform'] == 'uhomes'].iloc[0]
            uhomes_success = self._extract_platform_content(property_id, uhomes_row, 'uhomes')
            
            if amber_success and uhomes_success:
                logger.info(f"✅ {property_id} content extraction complete")
                return True
            else:
                logger.warning(f"⚠️ {property_id} content extraction incomplete")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting content for {property_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_platform_content(self, property_id: str, row: pd.Series, platform: str) -> bool:
        """
        Extract content for a single platform
        
        Args:
            property_id: Property ID
            row: Row from Raw_Scraped_Data
            platform: 'amber' or 'uhomes'
            
        Returns:
            Success status
        """
        logger.info(f"\n  Extracting {platform.upper()} content...")
        
        try:
            # Load API data from SCRAPED DATA in sheet (NOT calling API)
            api_data = None
            raw_json = row.get('Raw_JSON_Data', '')
            if raw_json and len(raw_json) > 100:
                try:
                    api_data = json.loads(raw_json)
                    logger.info(f"    Loaded scraped API data from sheet")
                except json.JSONDecodeError:
                    # Try backup file if sheet data is truncated
                    backup_file = Path('scraped_json_backup') / f"{property_id}_{platform}_raw.json"
                    if backup_file.exists():
                        with open(backup_file, 'r') as f:
                            api_data = json.load(f)
                        logger.info(f"    Loaded API data from backup file (sheet data truncated)")
                    else:
                        logger.warning(f"    No API data found")
            
            if not api_data:
                logger.error(f"    ❌ No API data available for {platform}")
                return False
            
            # Extract structured data from JSON columns
            structured_data = self._load_structured_data(row)
            
            # Rule-based extraction
            logger.info(f"    📊 Rule-based extraction...")
            rule_extracted = self.rule_extractor.extract_from_api_data(api_data, platform)
            
            # Extract section-by-section content
            # Pass api_data directly so extraction methods can access meta, etc.
            sections_data = self._extract_all_sections(
                property_id, platform, row['Property_Name'], 
                api_data, structured_data, rule_extracted
            )
            
            # Store in Content_Extraction sheet (new sheet for step 1)
            self._store_content_extraction(property_id, platform, row['Property_Name'], sections_data)
            
            logger.info(f"    ✅ {platform} content extracted and stored")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ Error extracting {platform} content: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_structured_data(self, row: pd.Series) -> Dict[str, Any]:
        """Load structured data from JSON columns"""
        structured = {}
        
        json_columns = {
            'Hero_Features_JSON': 'hero_features',
            'Payment_Details_JSON': 'payment_details',
            'Offers_JSON': 'offers',
            'Nearby_Properties_JSON': 'nearby_properties',
            'Room_Types_JSON': 'room_types',
            'Property_Metadata_JSON': 'property_metadata',
            'Videos_JSON': 'videos',
            'Virtual_Tours_JSON': 'virtual_tours'
        }
        
        for col_name, key_name in json_columns.items():
            if col_name in row and row[col_name]:
                try:
                    structured[key_name] = json.loads(row[col_name])
                except:
                    pass
        
        return structured
    
    def _extract_all_sections(self, 
                              property_id: str,
                              platform: str,
                              property_name: str,
                              api_data: Dict[str, Any],
                              structured_data: Dict[str, Any],
                              rule_extracted: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract content for all sections
        
        Returns:
            Dictionary mapping section_name -> section_data
        """
        sections = {}
        
        # Section order
        section_order = [
            'Hero & Media',
            'Offers',
            'About Property',
            'Room Types',
            'Amenities',
            'Payment',
            'Cancellation',
            'FAQs',
            'Nearby Properties',
            'University Links'
        ]
        
        for section_name in section_order:
            section_data = self._extract_section_content(
                section_name, api_data, structured_data, rule_extracted, platform
            )
            sections[section_name] = section_data
        
        return sections
    
    def _extract_section_content(self,
                                 section_name: str,
                                 api_data: Dict[str, Any],
                                 structured_data: Dict[str, Any],
                                 rule_extracted: Dict[str, Any],
                                 platform: str) -> Dict[str, Any]:
        """
        Extract content for a specific section
        
        Returns:
            Dictionary with extracted content (no scores)
        """
        section_data = {
            'section_name': section_name,
            'platform': platform,
            'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if section_name == 'Hero & Media':
            # Get room types data if available to include room type media
            room_types_section = None
            if platform == 'amber' and api_data:
                # We'll extract room types media in hero media extraction
                pass
            elif platform == 'uhomes' and api_data:
                room_types_data = api_data.get('room_types', {})
                room_types_section = room_types_data
            
            section_data.update(self._extract_hero_media(structured_data, rule_extracted, api_data, platform, room_types_section))
        
        elif section_name == 'Offers':
            section_data.update(self._extract_offers(structured_data, rule_extracted))
        
        elif section_name == 'About Property':
            section_data.update(self._extract_about_property(api_data, rule_extracted, platform))
        
        elif section_name == 'Room Types':
            section_data.update(self._extract_room_types(structured_data, rule_extracted, platform, api_data))
        
        elif section_name == 'Amenities':
            section_data.update(self._extract_amenities(api_data, rule_extracted, platform))
        
        elif section_name == 'Payment':
            section_data.update(self._extract_payment(structured_data, rule_extracted, api_data, platform))
        
        elif section_name == 'Cancellation':
            section_data.update(self._extract_cancellation(api_data, rule_extracted, platform))
        
        elif section_name == 'FAQs':
            section_data.update(self._extract_faqs(api_data, rule_extracted, platform))
        
        elif section_name == 'Nearby Properties':
            section_data.update(self._extract_nearby_properties(structured_data, rule_extracted, api_data))
        
        elif section_name == 'University Links':
            section_data.update(self._extract_university_links(api_data, rule_extracted, platform))
        
        return section_data
    
    def _extract_hero_media(self, structured_data: Dict, rule_extracted: Dict, api_data: Dict = None, platform: str = 'amber', room_types_data: Dict = None) -> Dict[str, Any]:
        """
        Extract Hero & Media content with granular counts
        
        Returns detailed media counts including:
        - Images (static photos)
        - Videos (all video content)
        - Video Tours (subset of videos - tour-specific videos)
        - Virtual Tours (all interactive tours)
        - 360° Tours (subset of virtual tours - panoramic)
        - 3D Tours (subset of virtual tours - 3D models)
        """
        hero_features = structured_data.get('hero_features', {})
        videos = structured_data.get('videos', [])
        virtual_tours = structured_data.get('virtual_tours', [])
        
        # Calculate accurate image count
        image_count = rule_extracted.get('image_count', 0)
        
        # For UHomes, count images from media array - USE COUNT FIELD (more accurate)
        if platform == 'uhomes' and api_data:
            media_array = api_data.get('media', [])
            for media_item in media_array:
                if media_item.get('type') == 'image':
                    # Use count field first (matches website), fall back to items length
                    count = media_item.get('count', 0)
                    if count > 0:
                        image_count = count
                        break
                    # Fall back to items length if count not available
                    items = media_item.get('items', [])
                    if items:
                        image_count = len(items)
                        break
        
        # Calculate accurate video count and identify video tours
        video_count = len(videos) if videos else 0
        video_tour_count = 0
        
        # Identify video tours (videos that are specifically tours)
        # Check video type, caption, or URL patterns
        # Handle both dict and string formats
        for video in videos:
            # Check if video is a dict or string
            if isinstance(video, dict):
                video_type = str(video.get('type', '')).lower()
                caption = str(video.get('caption', '')).lower()
                url = str(video.get('url', '') + video.get('path', '')).lower()
            else:
                # If video is a string (URL or path), check the string itself
                video_type = ''
                caption = ''
                url = str(video).lower()
            
            # Consider it a video tour if:
            # - Type contains 'tour'
            # - Caption contains 'tour', 'walkthrough', 'walk through'
            # - URL contains tour-related keywords
            is_tour = (
                'tour' in video_type or
                'tour' in caption or
                'walkthrough' in caption or
                'walk through' in caption or
                'tour' in url
            )
            
            if is_tour:
                video_tour_count += 1
        
        # For UHomes, count videos from media array - USE COUNT FIELD (more accurate)
        if platform == 'uhomes' and api_data:
            media_array = api_data.get('media', [])
            for media_item in media_array:
                if media_item.get('type') == 'video':
                    # Use count field first (matches website), fall back to items length
                    count = media_item.get('count', 0)
                    if count > 0:
                        video_count = count
                        # Try to identify video tours from items if available
                        items = media_item.get('items', [])
                        if items:
                            for item in items:
                                item_type = str(item.get('type', '')).lower()
                                item_source = str(item.get('source', '')).lower()
                                if 'tour' in item_type or 'tour' in item_source:
                                    video_tour_count += 1
                        break
                    # Fall back to items length if count not available
                    items = media_item.get('items', [])
                    if items:
                        video_count = len(items)
                        # Try to identify video tours from items
                        for item in items:
                            item_type = str(item.get('type', '')).lower()
                            item_source = str(item.get('source', '')).lower()
                            if 'tour' in item_type or 'tour' in item_source:
                                video_tour_count += 1
                        break
            
            # Check for live videos - USE COUNT FIELD
            for media_item in media_array:
                if media_item.get('type') == 'live':
                    count = media_item.get('count', 0)
                    if count > 0:
                        # Lives are separate from regular videos
                        # Note: We'll track this separately
                        pass
            
            # Also check digital_human_videos (these are usually tours/lives)
            tips = api_data.get('tips', {})
            digital_videos = tips.get('digital_human_videos', {})
            if digital_videos and digital_videos.get('items'):
                digital_count = len(digital_videos.get('items', []))
                # Don't add to video_count - these are separate "lives"
                # video_tour_count += digital_count  # Digital human videos are typically tours
        
        # Analyze virtual tours to separate 360° and 3D tours
        virtual_tour_count = len(virtual_tours) if virtual_tours else 0
        tour_360_count = 0
        tour_3d_count = 0
        live_count = 0  # Track live videos separately
        by_tenant_count = 0  # Track tenant-uploaded media
        
        for tour in virtual_tours:
            # Handle both dict and string formats
            if isinstance(tour, dict):
                tour_type = str(tour.get('type', '')).lower()
                is_360 = tour.get('is_360_tour', False)
                is_3d = tour.get('is_3d_tour', False)
            else:
                # If tour is a string (URL or path), check the string itself
                tour_type = str(tour).lower()
                is_360 = False
                is_3d = False
            
            # Check type string for keywords
            if not is_360 and not is_3d:
                if '360' in tour_type or 'virtual' in tour_type or 'vr' in tour_type:
                    is_360 = True
                elif '3d' in tour_type or '3-d' in tour_type:
                    is_3d = True
            
            if is_360:
                tour_360_count += 1
            elif is_3d:
                tour_3d_count += 1
        
        # For Amber API, check virtual_views directly if available
        if platform == 'amber' and api_data:
            virtual_views = api_data.get('data', {}).get('virtual_views', [])
            if virtual_views:
                for view in virtual_views:
                    view_type = str(view.get('type', '')).lower()
                    if '360' in view_type or 'virtual' in view_type or 'vr' in view_type:
                        if '3d' not in view_type and '3-d' not in view_type:
                            tour_360_count += 1
                    elif '3d' in view_type or '3-d' in view_type:
                        tour_3d_count += 1
        
        # For UHomes, check VR links and lives from media array - USE COUNT FIELD
        if platform == 'uhomes' and api_data:
            media_array = api_data.get('media', [])
            for media_item in media_array:
                media_type = media_item.get('type', '')
                count = media_item.get('count', 0)
                
                if media_type == 'vr_link':
                    # Use count field (matches website exactly)
                    if count > 0:
                        tour_360_count += count
                        virtual_tour_count += count
                    else:
                        # Fall back to items length
                        items = media_item.get('items', [])
                        if items:
                            tour_360_count += len(items)
                            virtual_tour_count += len(items)
                
                elif media_type == 'live':
                    # Track live videos separately
                    if count > 0:
                        live_count = count
                    else:
                        items = media_item.get('items', [])
                        if items:
                            live_count = len(items)
                
                elif media_type == 'by_tenant':
                    # Track tenant-uploaded media
                    if count > 0:
                        by_tenant_count = count
                    else:
                        items = media_item.get('items', [])
                        if items:
                            by_tenant_count = len(items)
        
        # ADD ROOM TYPE MEDIA TO TOTALS
        room_type_images = 0
        room_type_videos = 0
        room_type_video_tours = 0
        room_type_virtual_tours = 0
        room_type_360_count = 0
        room_type_3d_count = 0
        
        # For Amber, fetch room types and count their media
        if platform == 'amber' and api_data:
            try:
                from src.scrapers.amber_api_scraper import AmberAPIScraper
                canonical_name = api_data.get('data', {}).get('canonical_name', '')
                if canonical_name:
                    amber_scraper = AmberAPIScraper()
                    room_types_data = amber_scraper.fetch_room_types(canonical_name)
                    
                    if room_types_data:
                        for room_type in room_types_data:
                            # Count images
                            room_images = room_type.get('images', [])
                            room_type_images += len(room_images)
                            
                            # Count videos
                            room_videos = room_type.get('videos', [])
                            room_type_videos += len(room_videos)
                            
                            # Count video tours
                            for video in room_videos:
                                video_type = str(video.get('type', '')).lower()
                                caption = str(video.get('caption', '')).lower()
                                if 'tour' in video_type or 'tour' in caption:
                                    room_type_video_tours += 1
                            
                            # Count virtual tours
                            room_virtual_views = room_type.get('virtual_views', [])
                            room_type_virtual_tours += len(room_virtual_views)
                            
                            for view in room_virtual_views:
                                view_type = str(view.get('type', '')).lower()
                                if '360' in view_type or 'virtual' in view_type or 'vr' in view_type:
                                    if '3d' not in view_type and '3-d' not in view_type:
                                        room_type_360_count += 1
                                elif '3d' in view_type or '3-d' in view_type:
                                    room_type_3d_count += 1
            except Exception as e:
                logger.warning(f"Could not fetch Amber room types for media count: {e}")
        
        # For UHomes, count room type media from API data
        # NOTE: For UHomes, hero image_count already includes room type images (from count field)
        # So we only add room type media if count field wasn't used
        if platform == 'uhomes' and api_data:
            # Check if we used count field (which already includes room types)
            used_count_field = False
            media_array = api_data.get('media', [])
            for media_item in media_array:
                if media_item.get('type') == 'image' and media_item.get('count', 0) > 0:
                    used_count_field = True
                    break
            
            if not used_count_field:
                # Only count room types if we didn't use count field
                room_types_data = api_data.get('room_types', {})
                room_type_items = room_types_data.get('room_type_items', [])
                
                for item in room_type_items:
                    media = item.get('media', {})
                    media_meta = media.get('meta', {})
                    
                    # Count images (only if count field wasn't used)
                    room_type_images += media_meta.get('image_count', 0)
                    
                    # Count videos
                    room_type_videos += media_meta.get('video_count', 0)
                    
                    # Count VR links (3D/360° tours)
                    vr_links = media.get('vr_link', []) or []
                    if vr_links:
                        room_type_virtual_tours += len(vr_links)
                        # Assume VR links are 360° tours (most common)
                        room_type_360_count += len(vr_links)
                    
                    # Check videos for tours
                    video_items = media.get('video', [])
                    for video_item in video_items:
                        source = str(video_item.get('source', '')).lower()
                        if 'tour' in source:
                            room_type_video_tours += 1
        
        # COMBINE HERO + ROOM TYPE MEDIA
        total_image_count = image_count + room_type_images
        total_video_count = video_count + room_type_videos
        total_video_tour_count = video_tour_count + room_type_video_tours
        total_virtual_tour_count = virtual_tour_count + room_type_virtual_tours
        total_360_count = tour_360_count + room_type_360_count
        total_3d_count = tour_3d_count + room_type_3d_count
        
        return {
            # TOTAL COUNTS (Hero + Room Types)
            'image_count': total_image_count,
            'video_count': total_video_count,
            'video_tour_count': total_video_tour_count,
            'virtual_tour_count': total_virtual_tour_count,
            'tour_360_count': total_360_count,
            'tour_3d_count': total_3d_count,
            'live_count': live_count,  # NEW: Live videos count
            'by_tenant_count': by_tenant_count,  # NEW: Tenant-uploaded media count
            # BREAKDOWN (for reference)
            'hero_image_count': image_count,
            'hero_video_count': video_count,
            'room_type_image_count': room_type_images,
            'room_type_video_count': room_type_videos,
            # FLAGS
            'has_360_tour': total_360_count > 0 or hero_features.get('has_360_tour', False),
            'has_3d_tour': total_3d_count > 0 or hero_features.get('has_3d_tour', False),
            'has_video_tour': total_video_tour_count > 0 or hero_features.get('has_video_tour', False),
            'has_map': hero_features.get('has_map', False),
            'has_price_display': hero_features.get('has_price_display', False),
            'videos': videos,
            'virtual_tours': virtual_tours,
            'hero_features': hero_features
        }
    
    def _extract_offers(self, structured_data: Dict, rule_extracted: Dict) -> Dict[str, Any]:
        """Extract Offers content"""
        offers = structured_data.get('offers', [])
        
        return {
            'offer_count': len(offers) if offers else 0,
            'offers': offers,
            'offer_types': list(set([o.get('type', '') for o in offers if o.get('type')]))
        }
    
    def _extract_about_property(self, api_data: Dict, rule_extracted: Dict, platform: str) -> Dict[str, Any]:
        """Extract About Property content - ALL descriptions"""
        if platform == 'amber':
            descriptions = api_data.get('data', {}).get('description', [])
            # Extract ALL descriptions, not just "about"
            all_texts = []
            description_dict = {}
            
            for desc in descriptions:
                name = desc.get('name', '')
                value = desc.get('value', '')
                if value:
                    all_texts.append(value)
                    description_dict[name] = value
            
            # Combine all descriptions
            combined_text = ' '.join(all_texts)
            word_count = len(combined_text.split()) if combined_text else 0
            
            # Also extract highlights, tags, location from Property_Metadata
            highlights = api_data.get('data', {}).get('highlights', [])
            tags = api_data.get('data', {}).get('tags', [])
            location = api_data.get('data', {}).get('location', {})
            meta = api_data.get('data', {}).get('meta', {})
            
            # Property info from meta
            property_info = {
                'unit_count': meta.get('unit_count'),
                'unit_types': meta.get('unit_types', []),
                'max_area': meta.get('max_area'),
                'min_area': meta.get('min_area'),
                'area_unit': meta.get('area_unit'),
                'max_bedroom_count': meta.get('max_bedroom_count'),
                'min_bedroom_count': meta.get('min_bedroom_count'),
                'max_bathroom_count': meta.get('max_bathroom_count'),
                'min_bathroom_count': meta.get('min_bathroom_count'),
                'year_of_construction': meta.get('year_of_construction')
            }
            
        else:  # uhomes
            about = api_data.get('about', {})
            about_text = about.get('text_strip_html', '') if isinstance(about, dict) else ''
            word_count = len(about_text.split()) if about_text else 0
            combined_text = about_text
            description_dict = {'about': about_text}
            highlights = []
            tags = []
            location = {}
            property_info = {}
        
        return {
            'word_count': word_count,
            'content': combined_text[:1000],  # First 1000 chars
            'has_content': bool(combined_text),
            'all_descriptions': description_dict,  # All description sections
            'highlights': highlights if isinstance(highlights, list) else [],
            'tags': tags if isinstance(tags, list) else [],
            'location': location if isinstance(location, dict) else {},
            'property_info': property_info
        }
    
    def _categorize_room_type(self, room_name: str, unit_type: str = None, type_id: int = None) -> str:
        """Categorize room type into: Ensuite, Non Ensuite, Studio"""
        name_lower = room_name.lower()
        
        # Check type_id for UHomes (8=Ensuite, 9=Non Ensuite, 2=Studio)
        if type_id == 8:
            return 'Ensuite'
        elif type_id == 9:
            return 'Non Ensuite'
        elif type_id == 2:
            return 'Studio'
        
        # Check unit_type for Amber
        if unit_type == 'studio':
            return 'Studio'
        elif unit_type == 'ensuite':
            return 'Ensuite'
        elif unit_type == 'non_ensuite':
            return 'Non Ensuite'
        
        # Check name patterns (order matters: check "non ensuite" BEFORE "ensuite")
        if 'studio' in name_lower:
            return 'Studio'
        elif ('non' in name_lower and 'ensuite' in name_lower) or 'shared bathroom' in name_lower:
            return 'Non Ensuite'
        elif 'ensuite' in name_lower or 'en-suite' in name_lower:
            return 'Ensuite'
        elif 'apartment' in name_lower:
            # Check if it has private bathroom (ensuite) or shared (non-ensuite)
            # Default to Ensuite for apartments, can be refined
            return 'Ensuite'
        
        return 'Unknown'
    
    def _extract_room_types(self, structured_data: Dict, rule_extracted: Dict, platform: str, api_data: Dict = None) -> Dict[str, Any]:
        """Extract Room Types content - ALL details including media counts, categories, and tenancies"""
        room_types = structured_data.get('room_types', [])
        
        total_room_images = 0
        total_room_videos = 0
        total_room_vr = 0
        total_tenancies = 0
        total_available_tenancies = 0  # Track available tenancies separately
        
        # Category tracking
        categories = {
            'Studio': [],
            'Ensuite': [],
            'Non Ensuite': [],
            'Unknown': []
        }
        
        if platform == 'uhomes' and room_types:
            # UHomes room_types is already a flattened array with all details
            room_list = []
            for room in room_types:
                # Extract all available fields
                image_count = room.get('image_count', 0)
                video_count = room.get('video_count', 0)
                vr_count = room.get('vr_link_count', 0)
                
                total_room_images += image_count
                total_room_videos += video_count
                total_room_vr += vr_count
                
                room_name = room.get('name', '')
                type_id = room.get('type_id')
                category = self._categorize_room_type(room_name, type_id=type_id)
                
                room_data = {
                    'name': room_name,
                    'category': category,  # NEW: Category
                    'type_id': type_id,
                    'sku': room.get('sku', ''),
                    'price': room.get('price'),
                    'currency': room.get('currency', ''),
                    'promo_price': room.get('promo_price'),
                    'area_sqm': room.get('area_sqm', {}),  # {min, max}
                    'area_sqft': room.get('area_sqft', {}),  # {min, max}
                    'bed_count': room.get('bed_count'),
                    'bathroom_count': room.get('bathroom_count'),
                    'kitchen_type': room.get('kitchen_type'),
                    'booking_status': room.get('booking_status'),
                    'image_count': image_count,  # Per room type
                    'video_count': video_count,  # Per room type
                    'vr_link_count': vr_count,  # Per room type
                    'has_360_tour': room.get('has_360_tour', False),
                    'images': room.get('images', []),
                    'tenancies': []  # Will be populated from API
                }
                room_list.append(room_data)
                categories[category].append(room_data)
            
            # Extract tenancies from API if available
            if api_data:
                room_types_data = api_data.get('room_types', {})
                room_type_items = room_types_data.get('room_type_items', [])
                
                # Recalculate totals from API data (more accurate)
                total_room_images = 0
                total_room_videos = 0
                total_room_vr = 0
                total_tenancies = 0
                total_available_tenancies = 0  # Reset available count
                
                # Map room types by name or type_id to add tenancies
                room_map = {room['name']: room for room in room_list}
                
                for room_item in room_type_items:
                    media = room_item.get('media', {})
                    media_meta = media.get('meta', {})
                    total_room_images += media_meta.get('image_count', 0)
                    total_room_videos += media_meta.get('video_count', 0)
                    total_room_vr += media_meta.get('vr_link_count', 0)
                    
                    # Extract tenancies
                    tenancies = room_item.get('tenancies', [])
                    room_type = room_item.get('room_type', {})
                    room_name = room_type.get('name', '')
                    
                    if room_name in room_map:
                        # Extract detailed tenancy information
                        tenancy_list = []
                        for tenancy in tenancies:
                            # Extract floor and view from room_type if available
                            room_type_obj = room_item.get('room_type', {})
                            orientation = room_type_obj.get('orientation', [])
                            view_directions = []
                            if orientation and isinstance(orientation, list):
                                for orient in orientation:
                                    if isinstance(orient, dict):
                                        view_name = orient.get('name', '')
                                        if view_name:
                                            view_directions.append(view_name)
                            
                            tenancy_data = {
                                'tenancy_id': tenancy.get('tenancy_id'),
                                'lease_time': tenancy.get('lease_time'),  # Duration in weeks
                                'lease_unit': tenancy.get('lease_unit', 'WEEK'),
                                'start_date': tenancy.get('start_date'),  # Move in date
                                'end_date': tenancy.get('end_date'),  # Move out date
                                'available_from': tenancy.get('start_date'),  # Available from
                                'rent_amount': tenancy.get('rent_amount', {}).get('amount'),
                                'rent_currency': tenancy.get('rent_amount', {}).get('abbr', 'GBP'),
                                'promo_amount': tenancy.get('promo_amount', {}).get('amount'),
                                'booking_status': tenancy.get('booking_status'),  # 1=available, 0=sold out
                                'is_available': tenancy.get('booking_status', 0) == 1,
                                'term': tenancy.get('term'),  # e.g., "2026/27"
                                'has_promo': tenancy.get('has_promo', 0) == 1,
                                'service_tags': tenancy.get('service_tags', []),
                                # NEW: Floor and View fields (may be null if not available in data)
                                'floor': None,  # Floor number - not directly available in UHomes JSON
                                'view': ', '.join(view_directions) if view_directions else None,  # View direction(s)
                                'orientation': view_directions if view_directions else []
                            }
                            tenancy_list.append(tenancy_data)
                            total_tenancies += 1
                            # Track available tenancies separately
                            if tenancy.get('booking_status', 0) == 1:
                                total_available_tenancies += 1
                        
                        room_map[room_name]['tenancies'] = tenancy_list
                        room_map[room_name]['tenancy_count'] = len(tenancy_list)
        elif platform == 'amber':
            # Amber has individual room types via /room_types endpoint
            room_list = []
            
            # Try to fetch individual room types from API
            if api_data:
                try:
                    # Import directly to avoid firecrawl dependency
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from src.scrapers.amber_api_scraper import AmberAPIScraper
                    canonical_name = api_data.get('data', {}).get('canonical_name', '')
                    if canonical_name:
                        amber_scraper = AmberAPIScraper()
                        room_types_data = amber_scraper.fetch_room_types(canonical_name)
                        
                        if room_types_data:
                            # Process each individual room type
                            for room_type in room_types_data:
                                room_name = room_type.get('name', '')
                                room_id = room_type.get('id')
                                
                                # Get room type details
                                meta = room_type.get('meta', {})
                                unit_type = meta.get('unit_type', '')
                                category = self._categorize_room_type(room_name, unit_type=unit_type)
                                
                                # Extract pricing
                                pricing = room_type.get('pricing', {})
                                min_price = pricing.get('min_price')
                                max_price = pricing.get('max_price')
                                
                                # Extract images
                                images = room_type.get('images', [])
                                image_count = len(images)
                                
                                # Extract tenancies from children field
                                children = room_type.get('children', [])
                                tenancy_list = []
                                
                                for child in children:
                                    child_meta = child.get('meta', {})
                                    child_pricing = child.get('pricing', {})
                                    
                                    # Extract tenancy details
                                    tenancy_data = {
                                        'tenancy_id': child.get('id'),
                                        'name': child.get('name', ''),
                                        'lease_time': child_meta.get('lease_duration'),  # Duration in weeks
                                        'lease_unit': child_meta.get('lease_duration_unit', 'WEEK'),
                                        'start_date': child_meta.get('available_from'),  # Move in date (format: DD-MM-YYYY)
                                        'end_date': child_meta.get('available_to'),  # Move out date
                                        'start_date_formatted': child_meta.get('available_from_formatted'),  # e.g., "6 Sep, 2025"
                                        'rent_amount': child_pricing.get('price'),  # Price per week
                                        'rent_currency': child_pricing.get('currency', 'GBP'),
                                        'is_available': child.get('available', False),
                                        'booking_status': 1 if child.get('available', False) else 0,
                                        # Floor and View from parent room type
                                        'floor': meta.get('floor'),  # Floor number/range
                                        'view': meta.get('facing'),  # View direction(s)
                                        'orientation': meta.get('facing', '').split(',') if meta.get('facing') else []
                                    }
                                    tenancy_list.append(tenancy_data)
                                    total_tenancies += 1
                                    # Track available tenancies separately
                                    if child.get('available', False):
                                        total_available_tenancies += 1
                                
                                # Create room type entry
                                room_data = {
                                    'name': room_name,
                                    'category': category,
                                    'type': unit_type,
                                    'room_id': room_id,
                                    'canonical_name': room_type.get('canonical_name'),
                                    'area': meta.get('area'),
                                    'area_unit': meta.get('area_unit', 'sqm'),
                                    'floor': meta.get('floor'),
                                    'view': meta.get('facing'),
                                    'orientation': meta.get('facing', '').split(',') if meta.get('facing') else [],
                                    'bedroom_count': meta.get('bedroom_count'),
                                    'bathroom_count': meta.get('bathroom_count'),
                                    'min_price': min_price,
                                    'max_price': max_price,
                                    'min_lease_duration': meta.get('min_lease_duration'),
                                    'max_lease_duration': meta.get('max_lease_duration'),
                                    'image_count': image_count,
                                    'images': [img.get('path') or img.get('base_path', '') for img in images],
                                    'tenancies': tenancy_list,
                                    'tenancy_count': len(tenancy_list)
                                }
                                
                                room_list.append(room_data)
                                categories[category].append(room_data)
                                
                                # Count media
                                total_room_images += image_count
                                videos = room_type.get('videos', [])
                                total_room_videos += len(videos)
                                virtual_views = room_type.get('virtual_views', [])
                                total_room_vr += len(virtual_views)
                            
                            logger.info(f"✅ Fetched {len(room_list)} individual room types with {total_tenancies} tenancies")
                        else:
                            # Fall back to categories if room_types endpoint fails
                            logger.warning("⚠️ Could not fetch room types, falling back to categories")
                            unit_types = structured_data.get('property_metadata', {}).get('property_info', {}).get('unit_types', [])
                            property_info = structured_data.get('property_metadata', {}).get('property_info', {})
                            unit_types_filtered = [ut for ut in unit_types if ut != 'student_accommodation']
                            
                            for unit_type in unit_types_filtered:
                                room_name = unit_type.replace('_', ' ').title()
                                category = self._categorize_room_type(room_name, unit_type=unit_type)
                                
                                room_data = {
                                    'name': room_name,
                                    'category': category,
                                    'type': unit_type,
                                    'tenancies': [],
                                    'tenancy_count': 0
                                }
                                room_list.append(room_data)
                                categories[category].append(room_data)
                except Exception as e:
                    logger.warning(f"Could not fetch Amber room types: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fall back to categories
                    unit_types = structured_data.get('property_metadata', {}).get('property_info', {}).get('unit_types', [])
                    property_info = structured_data.get('property_metadata', {}).get('property_info', {})
                    unit_types_filtered = [ut for ut in unit_types if ut != 'student_accommodation']
                    
                    for unit_type in unit_types_filtered:
                        room_name = unit_type.replace('_', ' ').title()
                        category = self._categorize_room_type(room_name, unit_type=unit_type)
                        
                        room_data = {
                            'name': room_name,
                            'category': category,
                            'type': unit_type,
                            'tenancies': [],
                            'tenancy_count': 0
                        }
                        room_list.append(room_data)
                        categories[category].append(room_data)
        else:
            room_list = []
        
        return {
            # Individual room types (e.g., "Gold Ensuite", "Silver Studio", "Bronze Ensuite Shared Lower Level")
            'room_type_count': len(room_types) if room_types else len(room_list),
            'room_types': room_list,  # List of individual room types with their details
            'has_prices': any(r.get('price') for r in room_list),
            'has_sizes': any(r.get('area_sqm') or r.get('area_sqft') or r.get('min_area') for r in room_list),
            'unit_types': structured_data.get('property_metadata', {}).get('property_info', {}).get('unit_types', []) if platform == 'amber' else [],
            # Room type media counts (separate from hero section)
            'total_room_images': total_room_images,
            'total_room_videos': total_room_videos,
            'total_room_vr_links': total_room_vr,
            # Room type categories (3 categories: Studio, Ensuite, Non Ensuite)
            'category_counts': {
                'Studio': len(categories['Studio']),
                'Ensuite': len(categories['Ensuite']),
                'Non Ensuite': len(categories['Non Ensuite']),
                'Unknown': len(categories['Unknown'])
            },
            'categories': categories,  # Grouped by category for easy access
            # Tenancy counts (tenancies within each room type)
            'total_tenancies': total_tenancies,
            'total_available_tenancies': total_available_tenancies,  # NEW: Available tenancies (matches website display)
            'total_sold_out_tenancies': total_tenancies - total_available_tenancies,  # NEW: Sold out tenancies
            'tenancies_per_room_type': {room['name']: len(room.get('tenancies', [])) for room in room_list},
            # Tenancy counts per category (all tenancies)
            'category_tenancy_counts': {
                'Studio': sum(len(room.get('tenancies', [])) for room in categories['Studio']),
                'Ensuite': sum(len(room.get('tenancies', [])) for room in categories['Ensuite']),
                'Non Ensuite': sum(len(room.get('tenancies', [])) for room in categories['Non Ensuite']),
                'Unknown': sum(len(room.get('tenancies', [])) for room in categories['Unknown'])
            },
            # Available tenancy counts per category (NEW: matches what website shows)
            'category_available_tenancy_counts': {
                'Studio': sum(1 for room in categories['Studio'] 
                              for t in room.get('tenancies', []) 
                              if t.get('booking_status', 0) == 1 or t.get('is_available', False)),
                'Ensuite': sum(1 for room in categories['Ensuite'] 
                               for t in room.get('tenancies', []) 
                               if t.get('booking_status', 0) == 1 or t.get('is_available', False)),
                'Non Ensuite': sum(1 for room in categories['Non Ensuite'] 
                                   for t in room.get('tenancies', []) 
                                   if t.get('booking_status', 0) == 1 or t.get('is_available', False)),
                'Unknown': sum(1 for room in categories['Unknown'] 
                               for t in room.get('tenancies', []) 
                               if t.get('booking_status', 0) == 1 or t.get('is_available', False))
            },
            # Structure: Categories (3) → Individual Room Types (e.g., 21) → Tenancies (multiple per room type)
            'hierarchy_summary': {
                'category_count': sum(1 for count in {
                    'Studio': len(categories['Studio']),
                    'Ensuite': len(categories['Ensuite']),
                    'Non Ensuite': len(categories['Non Ensuite']),
                    'Unknown': len(categories['Unknown'])
                }.values() if count > 0),
                'individual_room_type_count': len(room_list),
                'total_tenancy_count': total_tenancies,
                'avg_tenancies_per_room_type': round(total_tenancies / len(room_list), 2) if room_list else 0
            }
        }
    
    def _extract_amenities(self, api_data: Dict, rule_extracted: Dict, platform: str) -> Dict[str, Any]:
        """Extract Amenities content"""
        if platform == 'amber':
            features = api_data.get('data', {}).get('features', [])
            # All amenities (no filter for Amber - all are property-level)
            all_amenity_list = []
            for feature_group in features:
                group_values = feature_group.get('values', [])
                for value in group_values:
                    all_amenity_list.append(value.get('name', ''))
            # Property-level = all amenities for Amber
            property_level_list = all_amenity_list
        else:  # uhomes
            features = api_data.get('features', [])
            
            # ALL amenities (no filter)
            all_amenity_list = []
            seen_all = set()  # Track duplicates (case-insensitive)
            for feature in features:
                name = feature.get('name', '').strip()
                if name:
                    name_lower = name.lower()
                    if name_lower not in seen_all:
                        seen_all.add(name_lower)
                        all_amenity_list.append(name)
            
            # Property-level amenities only (exclude room-level: Kitchen/Bedroom/Bathroom/General)
            # Property-level sub_types: 11 (Safety), 55 (Property Services), 56 (Shared Community),
            # 57 (Fitness & Recreation), 58 (Outdoor Features)
            property_level_subtypes = [11, 55, 56, 57, 58]
            property_level_list = []
            seen_property = set()  # Track duplicates (case-insensitive)
            
            for feature in features:
                sub_type = feature.get('sub_type')
                if sub_type in property_level_subtypes:
                    name = feature.get('name', '').strip()
                    if name:
                        name_lower = name.lower()
                        if name_lower not in seen_property:
                            seen_property.add(name_lower)
                            property_level_list.append(name)
        
        return {
            # Property-level (shown on website)
            'amenity_count': len(property_level_list),
            'amenities': property_level_list,
            # All amenities (including room-level)
            'all_amenity_count': len(all_amenity_list),
            'all_amenities': all_amenity_list,
            'rule_based_count': rule_extracted.get('amenity_count', 0)
        }
    
    def _extract_payment(self, structured_data: Dict, rule_extracted: Dict, api_data: Dict = None, platform: str = 'amber') -> Dict[str, Any]:
        """Extract Payment content - includes all payment details"""
        payment_details = structured_data.get('payment_details', {})
        payment_policies = []  # List of payment policies found
        
        # Check cancellation/refund policy text for guarantor mentions (for UHomes)
        if platform == 'uhomes' and api_data:
            # Check cancellation policy text
            rules = api_data.get('rules', [])
            for rule in rules:
                if rule.get('policy_type') == 'cancel':
                    policy_text_obj = rule.get('policy_text', {})
                    policy_text = policy_text_obj.get('text', '') if isinstance(policy_text_obj, dict) else (policy_text_obj if isinstance(policy_text_obj, str) else '')
                    if policy_text and 'guarantor' in policy_text.lower():
                        text_lower = policy_text.lower()
                        
                        # Check for negative phrases first (no guarantor required)
                        negative_phrases = ['no guarantor', 'guarantor not required', 'guarantor not needed', 
                                          'not require a guarantor', 'guarantor: not', 'guarantor not',
                                          'is not required', 'not required', 'does not require']
                        has_negative = any(phrase in text_lower for phrase in negative_phrases)
                        
                        if has_negative:
                            # Explicitly says no guarantor required - set to False
                            payment_details['guarantor_required'] = False
                            if not payment_details.get('guarantor_details'):
                                # Extract the relevant sentence for context
                                sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                                payment_details['guarantor_details'] = {
                                    'source': 'cancellation_policy',
                                    'text': '. '.join(sentences[:2]) if sentences else policy_text[:300],
                                    'note': 'Explicitly states no guarantor required'
                                }
                        else:
                            # Check for positive phrases (guarantor required)
                            positive_phrases = ['guarantor must', 'guarantor is required', 'guarantor required', 
                                               'must sign', 'guarantor and', 'guarantor will']
                            has_positive = any(phrase in text_lower for phrase in positive_phrases)
                            
                            if has_positive:
                                # Guarantor is required - extract details
                                payment_details['guarantor_required'] = True
                                if not payment_details.get('guarantor_details'):
                                    # Extract sentences containing guarantor for context
                                    sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                                    payment_details['guarantor_details'] = {
                                        'source': 'cancellation_policy',
                                        'text': '. '.join(sentences[:3]) if sentences else policy_text[:500],
                                        'note': 'Extracted from cancellation policy text'
                                    }
                            else:
                                # Mentioned but unclear - set to None/NA
                                payment_details['guarantor_required'] = None  # NA/Unclear
                                if not payment_details.get('guarantor_details'):
                                    sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                                    payment_details['guarantor_details'] = {
                                        'source': 'cancellation_policy',
                                        'text': '. '.join(sentences[:2]) if sentences else policy_text[:300],
                                        'note': 'Guarantor mentioned but requirement unclear - needs review'
                                    }
                        break
        
        # Also extract directly from API data if available for more details
        if api_data and platform == 'amber':
            descriptions = api_data.get('data', {}).get('description', [])
            
            # Extract detailed payment information from API and count policies
            for desc in descriptions:
                tag = desc.get('tag', '')
                name = desc.get('name', '')
                value = desc.get('value', '')
                short_text = desc.get('short_text', '')
                display_name = desc.get('display_name', '')
                
                # Count payment policies (main 4 policies, excluding holding_fee as it's part of installment)
                if name == 'payment':
                    # Main payment policies (4): installment_plan, mode_of_payment, guarantor_requirement, booking_deposit
                    if tag in ['payment_instalment_plan', 'mode_of_payment', 'guarantor_requirement', 'booking_deposit']:
                        payment_policies.append({
                            'tag': tag,
                            'display_name': display_name,
                            'short_text': short_text,
                            'value': value
                        })
                
                # Installment plan details
                if tag == 'payment_instalment_plan' and not payment_details.get('installment_details'):
                    payment_details['installment_details'] = {
                        'value': value,
                        'short_text': short_text,
                        'display_name': display_name
                    }
                
                # Payment method details (includes exclusions)
                if tag == 'mode_of_payment' and not payment_details.get('payment_method_details'):
                    payment_details['payment_method_details'] = {
                        'value': value,
                        'short_text': short_text,
                        'display_name': display_name
                    }
                
                # Guarantor requirement details
                if tag == 'guarantor_requirement' and not payment_details.get('guarantor_details'):
                    payment_details['guarantor_details'] = {
                        'value': value,
                        'short_text': short_text,
                        'display_name': display_name
                    }
        
        # Get full payment info from structured data
        booking_deposit = payment_details.get('booking_deposit')
        
        return {
            'installment_options': payment_details.get('installment_options', []),
            'payment_methods': payment_details.get('payment_methods', []),
            'guarantor_required': payment_details.get('guarantor_required'),  # Can be True, False, or None (NA)
            'deposit': payment_details.get('deposit', {}),
            'holding_fee': payment_details.get('holding_fee', {}),
            'booking_deposit': booking_deposit,  # NEW: Include booking deposit
            'has_deposit_info': bool(payment_details.get('deposit')),
            'has_holding_fee': bool(payment_details.get('holding_fee')),
            'has_booking_deposit': bool(booking_deposit),
            'has_installment': bool(payment_details.get('installment_options')),
            # Include detailed payment information
            'installment_details': payment_details.get('installment_details', {}),
            'payment_method_details': payment_details.get('payment_method_details', {}),
            'guarantor_details': payment_details.get('guarantor_details', {}),
            # Payment policies count (should be 4)
            'payment_policy_count': len(payment_policies),
            'payment_policies': payment_policies,
            # Include full payment_details for complete information
            'full_payment_details': payment_details
        }
    
    def _extract_cancellation(self, api_data: Dict, rule_extracted: Dict, platform: str) -> Dict[str, Any]:
        """Extract Cancellation content - extracts ALL cancellation policies"""
        # Extract from API data if available
        has_policy = False
        cooling_off = 0
        policy_text = ''
        cancellation_details = []
        
        if platform == 'amber':
            descriptions = api_data.get('data', {}).get('description', [])
            
            # Extract ALL cancellation policies (not just the first one)
            cancellation_tags = ['cooling_off_period', 'no_visa_no_pay', 'no_place_no_pay', 'replacement_tenant_found']
            
            for desc in descriptions:
                tag = desc.get('tag', '')
                name = desc.get('name', '')
                value = desc.get('value', '')
                short_text = desc.get('short_text', '')
                display_name = desc.get('display_name', '')
                
                # Check if it's a cancellation policy
                if tag in cancellation_tags or 'cancellation' in name.lower():
                    has_policy = True
                    
                    # Build policy text (combine all policies)
                    if policy_text:
                        policy_text += '\n\n---\n\n'
                    
                    if display_name:
                        policy_text += f"## {display_name}\n\n"
                    elif name:
                        policy_text += f"## {name}\n\n"
                    
                    if short_text:
                        policy_text += f"{short_text}\n\n"
                    
                    policy_text += value
                    
                    # Store individual policy details
                    cancellation_details.append({
                        'tag': tag,
                        'name': name,
                        'display_name': display_name,
                        'short_text': short_text,
                        'value': value,
                        'policy_applicable': desc.get('policy_applicable', 'false')
                    })
            
            # If no cancellation policies found by tag, check by name/value
            if not cancellation_details:
                for desc in descriptions:
                    name = desc.get('name', '').lower()
                    value = desc.get('value', '')
                    if 'cancellation' in name or 'cancellation' in value.lower():
                        has_policy = True
                        policy_text = value
                        cancellation_details.append({
                            'name': desc.get('name', ''),
                            'value': value,
                            'tag': desc.get('tag', '')
                        })
                        break
        else:  # uhomes
            # Extract from rules array where policy_type == 'cancel'
            rules = api_data.get('rules', [])
            if rules:
                cancel_rules = [r for r in rules if isinstance(r, dict) and r.get('policy_type') == 'cancel']
                if cancel_rules:
                    has_policy = True
                    for rule in cancel_rules:
                        policy_text_obj = rule.get('policy_text', {})
                        if isinstance(policy_text_obj, dict):
                            text = policy_text_obj.get('text', '')
                            if text:
                                policy_text = text if not policy_text else policy_text + '\n\n' + text
                                cancellation_details.append({
                                    'policy_type': rule.get('policy_type', ''),
                                    'policy_text': text,
                                    'title': rule.get('title', '')
                                })
                        elif isinstance(policy_text_obj, str):
                            policy_text = policy_text_obj if not policy_text else policy_text + '\n\n' + policy_text_obj
                            cancellation_details.append({
                                'policy_type': rule.get('policy_type', ''),
                                'policy_text': policy_text_obj,
                                'title': rule.get('title', '')
                            })
            
            # Also check if cancellation is mentioned in about text
            if not has_policy:
                about = api_data.get('about', {})
                if isinstance(about, dict):
                    about_text = about.get('text', '') or about.get('text_strip_html', '')
                    if about_text and 'cancellation' in about_text.lower():
                        has_policy = True
                        policy_text = about_text
        
        return {
            'has_cancellation_policy': has_policy,
            'cooling_off_period': cooling_off,
            'has_content': has_policy,
            'policy_text': policy_text,  # Full policy text (all policies combined)
            'policy_text_preview': policy_text[:1000] if policy_text else '',  # Preview for quick view
            'cancellation_details': cancellation_details,
            'detail_count': len(cancellation_details),
            # Individual policy flags
            'has_cooling_off': any(d.get('tag') == 'cooling_off_period' for d in cancellation_details),
            'has_no_visa_no_pay': any(d.get('tag') == 'no_visa_no_pay' for d in cancellation_details),
            'has_no_place_no_pay': any(d.get('tag') == 'no_place_no_pay' for d in cancellation_details),
            'has_replacement_tenant': any(d.get('tag') == 'replacement_tenant_found' for d in cancellation_details)
        }
    
    def _extract_faqs(self, api_data: Dict, rule_extracted: Dict, platform: str) -> Dict[str, Any]:
        """Extract FAQs content"""
        faqs = []
        faq_list = []
        
        if platform == 'amber':
            faqs = api_data.get('data', {}).get('faqs', [])
            faq_list = [{'question': f.get('question', ''), 'answer': f.get('answer', '')} for f in faqs]
        else:  # uhomes
            # Check multiple possible locations for FAQs (same as rule_based_extractor)
            # Check 'faq' key first
            faqs = api_data.get('faq', [])
            # Check 'features_faq' if 'faq' is empty
            if not faqs or len(faqs) == 0:
                faqs = api_data.get('features_faq', [])
            
            faq_list = [{'question': f.get('question') or f.get('title', ''), 
                        'answer': f.get('answer') or f.get('content', '')} for f in faqs]
        
        faq_count = len(faq_list)
        return {
            'faq_count': faq_count,
            'faqs': faq_list,
            'has_content': faq_count > 0,
            'rule_based_count': rule_extracted.get('faq_count', 0)
        }
    
    def _extract_nearby_properties(self, structured_data: Dict, rule_extracted: Dict, api_data: Dict = None) -> Dict[str, Any]:
        """Extract Nearby Properties content"""
        nearby = structured_data.get('nearby_properties', [])
        
        # Fallback: Check API data directly if not in structured_data
        if not nearby and api_data:
            # Check 'nearby_properties' key first
            nearby = api_data.get('nearby_properties', [])
            # Check 'nearby' key (UHomes uses this)
            if not nearby:
                nearby = api_data.get('nearby', [])
            # Check tips for similar properties (UHomes)
            if not nearby:
                tips = api_data.get('tips', {})
                if isinstance(tips, dict):
                    nearby = tips.get('similar_properties', [])
            # Check meta for similar properties (Amber)
            if not nearby:
                meta = api_data.get('data', {}).get('meta', {}) if isinstance(api_data.get('data'), dict) else {}
                if isinstance(meta, dict):
                    nearby = meta.get('similar_properties', [])
        
        property_count = len(nearby) if nearby else 0
        
        return {
            'property_count': property_count,
            'properties': nearby[:10] if nearby else [],  # First 10
            'has_content': property_count > 0,
            'has_prices': any(p.get('price') for p in nearby) if nearby else False
        }
    
    def _extract_university_links(self, api_data: Dict, rule_extracted: Dict, platform: str) -> Dict[str, Any]:
        """Extract University Links content"""
        universities = []
        
        if platform == 'amber':
            # Extract from meta.distances
            meta = api_data.get('data', {}).get('meta', {})
            distances = meta.get('distances', []) if isinstance(meta, dict) else []
            
            # Filter for universities/colleges
            for dist in distances:
                if isinstance(dist, dict):
                    place = dist.get('place', '')
                    distance = dist.get('distance', '')
                    # Check if it's a university/college
                    if any(keyword in place.lower() for keyword in ['university', 'college', 'institute', 'school']):
                        universities.append({
                            'name': place,
                            'distance': distance
                        })
        else:  # uhomes
            # UHomes stores university/school data in 'school' object (singular)
            school = api_data.get('school', {})
            if school and isinstance(school, dict):
                school_name = school.get('school_name', '')
                distance = school.get('distance', '')
                if school_name:
                    universities.append({
                        'name': school_name,
                        'distance': distance if distance else None
                    })
            
            # Also check nearby array (fallback - usually empty)
            nearby = api_data.get('nearby', [])
            if nearby:
                for location in nearby:
                    if isinstance(location, dict):
                        name = location.get('name') or location.get('title', '')
                        distance = location.get('distance', '')
                        # Check if it's a university/college
                        if name and any(keyword in name.lower() for keyword in ['university', 'college', 'institute', 'school']):
                            universities.append({
                                'name': name,
                                'distance': distance
                            })
            
            # Check schools array (plural) if it exists
            schools = api_data.get('schools', [])
            if schools and isinstance(schools, list):
                for s in schools:
                    if isinstance(s, dict):
                        school_name = s.get('school_name', '')
                        distance = s.get('distance', '')
                        if school_name:
                            universities.append({
                                'name': school_name,
                                'distance': distance if distance else None
                            })
        
        # Use rule-based extraction if available and no API data
        if not universities:
            rule_universities = rule_extracted.get('universities', [])
            if rule_universities:
                universities = rule_universities
        
        university_count = len(universities)
        return {
            'university_count': university_count,
            'universities': universities,
            'has_content': university_count > 0,
            'has_distances': any(u.get('distance') for u in universities) if universities else False
        }
    
    def _store_content_extraction(self, 
                                  property_id: str,
                                  platform: str,
                                  property_name: str,
                                  sections_data: Dict[str, Dict[str, Any]]):
        """
        Store extracted content in Content_Extraction sheet
        
        Creates/updates Content_Extraction sheet with extracted data
        """
        import time
        
        # Ensure sheet exists (with retry and delay)
        sheet_exists = False
        headers = [
            'Property_ID',
            'Platform',
            'Property_Name',
            'Section_Name',
            'Content_JSON',  # All extracted content as JSON
            'Item_Count',  # Count of items (amenities, FAQs, room types, etc.)
            'Word_Count',  # Word count for text sections
            'Image_Count',  # Image count for media sections
            'Video_Count',  # Video count
            'Virtual_Tour_Count',  # Virtual tour count
            'Tenancy_Count',  # NEW: Count of tenancies (for Room Types section)
            'Room_Category_Count',  # NEW: Count of room categories (Studio/Ensuite/Non Ensuite)
            'Has_Content',  # Boolean - does section have content?
            'Extracted_At'
        ]
        
        for attempt in range(3):
            try:
                # Try to read sheet
                try:
                    df = self.sheets.read_sheet('Content_Extraction')
                    # Check if headers need updating
                    current_headers = list(df.columns)
                    if len(current_headers) != len(headers) or current_headers != headers:
                        logger.info("    Updating Content_Extraction sheet headers...")
                        self.sheets.setup_headers('Content_Extraction', headers)
                        time.sleep(2)
                    sheet_exists = True
                    break
                except (ValueError, Exception) as e:
                    # Sheet doesn't exist or has issues - create/recreate
                    logger.info("    Creating/Recreating Content_Extraction sheet...")
                    try:
                        # Try to delete existing sheet if it exists
                        try:
                            worksheet = self.sheets.workbook.worksheet('Content_Extraction')
                            self.sheets.workbook.del_worksheet(worksheet)
                            time.sleep(2)
                        except:
                            pass  # Sheet doesn't exist, continue
                        
                        self.sheets.create_sheet('Content_Extraction', rows=10000, cols=20)
                        time.sleep(2)  # Wait after creation
                        
                        # Setup headers
                        self.sheets.setup_headers('Content_Extraction', headers)
                        time.sleep(2)  # Wait after headers
                        sheet_exists = True
                        break
                    except Exception as e2:
                        if attempt < 2:
                            logger.warning(f"    Retry {attempt + 1}/3 after delay...")
                            time.sleep(5)
                        else:
                            raise
            except Exception as e:
                if attempt < 2:
                    logger.warning(f"    Retry {attempt + 1}/3 after delay...")
                    time.sleep(5)
                else:
                    raise
        
        # Prepare all rows first (batch operation)
        rows_to_append = []
        
        # Store each section
        for section_name, section_data in sections_data.items():
            # Calculate counts
            item_count = 0
            word_count = section_data.get('word_count', 0)
            image_count = section_data.get('image_count', 0)
            video_count = section_data.get('video_count', 0)
            virtual_tour_count = section_data.get('virtual_tour_count', 0)
            has_content = False
            
            # Determine item_count and has_content based on section
            if section_name == 'Hero & Media':
                has_content = image_count > 0 or video_count > 0 or virtual_tour_count > 0
            elif section_name == 'Offers':
                item_count = section_data.get('offer_count', 0)
                has_content = item_count > 0
            elif section_name == 'About Property':
                has_content = section_data.get('has_content', False)
            elif section_name == 'Room Types':
                item_count = section_data.get('room_type_count', 0)
                # Also check unit_types for Amber
                unit_types = section_data.get('unit_types', [])
                if unit_types and item_count == 0:
                    # Filter out 'student_accommodation' as it's not a room type
                    unit_types_filtered = [ut for ut in unit_types if ut != 'student_accommodation']
                    item_count = len(unit_types_filtered)
                has_content = item_count > 0
                # Note: Tenancy count is stored separately in the data, not in item_count
                # item_count represents room types, tenancies are in total_tenancies field
            elif section_name == 'Amenities':
                item_count = section_data.get('amenity_count', 0)
                has_content = item_count > 0
            elif section_name == 'Payment':
                has_content = bool(section_data.get('installment_options') or 
                                 section_data.get('payment_methods') or
                                 section_data.get('deposit') or
                                 section_data.get('holding_fee') or
                                 section_data.get('booking_deposit') or
                                 section_data.get('has_deposit_info') or
                                 section_data.get('has_installment'))
                # Count payment POLICIES (not options/methods) - should be 4
                # Main policies: Pay In Instalment, Mode Of Payment, Guarantor Requirement, Booking Deposit
                item_count = section_data.get('payment_policy_count', 0)
                # Fallback: count policies if payment_policy_count not available
                if item_count == 0:
                    # Count distinct payment policy tags
                    policies = section_data.get('payment_policies', [])
                    if policies:
                        item_count = len(policies)
                    else:
                        # Fallback to counting main payment items
                        item_count = (1 if section_data.get('installment_options') else 0) + \
                                   (1 if section_data.get('payment_methods') else 0) + \
                                   (1 if section_data.get('guarantor_required') else 0) + \
                                   (1 if section_data.get('booking_deposit') else 0)
            elif section_name == 'Cancellation':
                has_content = section_data.get('has_cancellation_policy', False) or bool(section_data.get('policy_text'))
                item_count = section_data.get('detail_count', 0)
            elif section_name == 'FAQs':
                item_count = section_data.get('faq_count', 0)
                has_content = item_count > 0
            elif section_name == 'Nearby Properties':
                item_count = section_data.get('property_count', 0)
                has_content = item_count > 0
            elif section_name == 'University Links':
                item_count = section_data.get('university_count', 0)
                has_content = item_count > 0
                # Update item_count if universities found
                if item_count > 0:
                    pass  # Already set
            
            # Calculate additional counts for Room Types
            tenancy_count = 0
            room_category_count = 0
            
            if section_name == 'Room Types':
                tenancy_count = section_data.get('total_tenancies', 0)
                category_counts = section_data.get('category_counts', {})
                # Count non-zero categories
                room_category_count = sum(1 for count in category_counts.values() if count > 0)
            
            # Prepare JSON content - optimize for large Room Types data
            content_json = json.dumps(section_data, ensure_ascii=False)
            
            # If content is too large (Google Sheets limit is 50,000 chars), optimize it
            if len(content_json) > 50000:
                # For Room Types, we can optimize by limiting tenancy details
                if section_name == 'Room Types' and isinstance(section_data, dict):
                    optimized_data = section_data.copy()
                    room_types = optimized_data.get('room_types', [])
                    
                    # Limit tenancies per room type to essential fields and first 5 tenancies
                    for room in room_types:
                        tenancies = room.get('tenancies', [])
                        if len(tenancies) > 5:
                            # Keep only first 5 tenancies with essential fields
                            room['tenancies'] = tenancies[:5]
                            room['tenancy_count'] = len(tenancies)  # Keep original count
                        
                        # Simplify tenancy data to essential fields only
                        for tenancy in room.get('tenancies', []):
                            # Keep only essential fields
                            essential_fields = {
                                'lease_time', 'start_date', 'end_date', 'rent_amount', 
                                'rent_currency', 'floor', 'view', 'is_available'
                            }
                            tenancy_keys = list(tenancy.keys())
                            for key in tenancy_keys:
                                if key not in essential_fields:
                                    del tenancy[key]
                    
                    # Remove large nested structures if still too big
                    content_json = json.dumps(optimized_data, ensure_ascii=False)
                    if len(content_json) > 50000:
                        # Further reduce - remove images arrays, keep only counts
                        for room in room_types:
                            if 'images' in room:
                                room['image_count'] = len(room['images'])
                                room['images'] = []  # Remove image URLs to save space
                        
                        content_json = json.dumps(optimized_data, ensure_ascii=False)
                        if len(content_json) > 50000:
                            # Last resort: further reduce tenancies per room type
                            logger.warning(f"    ⚠️  Content_JSON still too large ({len(content_json)} chars), reducing tenancies...")
                            for room in room_types:
                                tenancies = room.get('tenancies', [])
                                if len(tenancies) > 3:
                                    room['tenancies'] = tenancies[:3]  # Keep only first 3
                                    room['tenancy_count'] = len(tenancies)  # Keep original count
                            
                            content_json = json.dumps(optimized_data, ensure_ascii=False)
                            if len(content_json) > 50000:
                                # Remove description text and other large fields
                                for room in room_types:
                                    room.pop('description', None)
                                    room.pop('features', None)
                                
                                content_json = json.dumps(optimized_data, ensure_ascii=False)
                                if len(content_json) > 50000:
                                    # Final fallback: create summary instead of full data
                                    logger.warning(f"    ⚠️  Content_JSON still too large ({len(content_json)} chars), creating summary...")
                                    summary_data = {
                                        'room_type_count': len(room_types),
                                        'total_tenancies': sum(r.get('tenancy_count', 0) for r in room_types),
                                        'category_counts': section_data.get('category_counts', {}),
                                        'room_types_summary': [
                                            {
                                                'name': r.get('name'),
                                                'category': r.get('category'),
                                                'tenancy_count': r.get('tenancy_count', 0),
                                                'min_price': r.get('min_price'),
                                                'max_price': r.get('max_price')
                                            }
                                            for r in room_types
                                        ],
                                        'note': 'Full data truncated due to size limit. See individual room types for details.'
                                    }
                                    content_json = json.dumps(summary_data, ensure_ascii=False)
            
            # Prepare row
            row_data = [
                property_id,
                platform,
                property_name,
                section_name,
                content_json,  # Optimized content as JSON
                item_count,
                word_count,
                image_count,
                video_count,
                virtual_tour_count,
                tenancy_count,  # NEW: Tenancy count
                room_category_count,  # NEW: Room category count
                has_content,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            rows_to_append.append(row_data)
        
        # Batch append all rows at once (reduces API calls)
        if rows_to_append:
            try:
                import time
                time.sleep(1)  # Small delay before batch write
                worksheet = self.sheets.workbook.worksheet('Content_Extraction')
                worksheet.append_rows(rows_to_append)
                logger.info(f"    ✅ Stored {len(rows_to_append)} sections in batch")
                time.sleep(1)  # Small delay after write
            except Exception as e:
                logger.error(f"    ❌ Error batch storing rows: {e}")
                # Fallback to individual appends
                import time
                for row_data in rows_to_append:
                    try:
                        time.sleep(0.5)  # Delay between individual appends
                        self.sheets.append_row('Content_Extraction', row_data)
                    except Exception as e2:
                        logger.error(f"    ❌ Error storing section {row_data[3]}: {e2}")
    
    def process_all_scraped(self) -> Dict[str, int]:
        """
        Process all scraped properties
        
        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "="*80)
        logger.info("CONTENT EXTRACTION - Step 1 (NO SCORING)")
        logger.info("="*80)
        
        # Get scraped properties
        try:
            input_df = self.sheets.read_sheet('Input_Properties')
            scraped_df = input_df[input_df['Status'] == 'scraped']
            
            if len(scraped_df) == 0:
                logger.info("No scraped properties found")
                return {'total': 0, 'success': 0, 'failed': 0}
            
            logger.info(f"Found {len(scraped_df)} properties to extract")
            
        except Exception as e:
            logger.error(f"Error reading properties: {e}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        stats = {'total': len(scraped_df), 'success': 0, 'failed': 0}
        
        # Process each property
        import time
        for idx, property_row in scraped_df.iterrows():
            property_id = property_row['Property_ID']
            
            try:
                # Small delay between properties to avoid Google Sheets API rate limits
                # (We're reading/writing to sheets, NOT calling property APIs)
                if idx > 0:
                    delay = 1  # 1 second delay between properties (reduced - not needed for reading)
                    time.sleep(delay)
                
                success = self.extract_property_content(property_id)
                
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing {property_id}: {e}")
                stats['failed'] += 1
                # Wait before retrying next property
                time.sleep(5)
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("CONTENT EXTRACTION - Complete")
        logger.info("="*80)
        logger.info(f"Total: {stats['total']}")
        logger.info(f"✅ Success: {stats['success']}")
        logger.info(f"❌ Failed: {stats['failed']}")
        logger.info("="*80)
        
        return stats


def main():
    print("\n" + "="*80)
    print("📊 STEP 1: CONTENT EXTRACTION (NO SCORING)")
    print("="*80)
    print("\nThis will:")
    print("1. Extract content from API data for all sections")
    print("2. Store extracted content in 'Content_Extraction' sheet")
    print("3. NO scoring - just extraction and storage")
    print("4. Makes data debuggable and verifiable")
    print("\n" + "="*80 + "\n")
    
    try:
        extractor = ContentExtractor()
        stats = extractor.process_all_scraped()
        
        print("\n" + "="*80)
        print("✅ CONTENT EXTRACTION COMPLETE!")
        print("="*80)
        print(f"Processed: {stats['total']} properties")
        print(f"Success: {stats['success']} properties")
        print(f"Failed: {stats['failed']} properties")
        print("="*80)
        print("\n📊 Check 'Content_Extraction' sheet to verify extracted data")
        print("   Next step: Run scoring on extracted content")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

