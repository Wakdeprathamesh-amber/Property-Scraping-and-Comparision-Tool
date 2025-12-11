"""
Rule-Based Data Extractor
Extracts counts and structured data from JSON/markdown WITHOUT AI
Used for accurate counting before semantic AI analysis
"""

import json
import re
from typing import Dict, Any, Optional, List
from src.utils.logger import setup_logger


class RuleBasedExtractor:
    """
    Extracts structured data using rule-based methods (no AI)
    Provides accurate counts for scoring and comparison
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    def extract_from_api_data(self, 
                             api_data: Optional[Dict[str, Any]], 
                             platform: str) -> Dict[str, Any]:
        """
        Extract structured counts from API JSON data
        
        Args:
            api_data: Raw API JSON response
            platform: 'amber' or 'uhomes'
            
        Returns:
            Dictionary with rule-based extracted counts and data
        """
        extracted = {
            'source': 'api',
            'has_api_data': api_data is not None
        }
        
        if not api_data:
            return extracted
        
        if platform == 'amber':
            extracted.update(self._extract_amber_api(api_data))
        elif platform == 'uhomes':
            extracted.update(self._extract_uhomes_api(api_data))
        
        return extracted
    
    def extract_from_markdown(self, markdown: str) -> Dict[str, Any]:
        """
        Extract counts from markdown using regex/pattern matching
        
        Args:
            markdown: Markdown content
            
        Returns:
            Dictionary with rule-based extracted counts
        """
        extracted = {
            'source': 'markdown',
            'word_count': len(markdown.split()) if markdown else 0,
            'char_count': len(markdown) if markdown else 0
        }
        
        # Extract images (markdown image syntax: ![alt](url))
        image_pattern = r'!\[.*?\]\((.*?)\)'
        image_matches = re.findall(image_pattern, markdown)
        extracted['images'] = image_matches  # Store URLs for deduplication
        extracted['image_count_markdown'] = len(image_matches)
        
        # Extract links (markdown link syntax: [text](url))
        link_pattern = r'\[.*?\]\((https?://.*?)\)'
        link_matches = re.findall(link_pattern, markdown)
        extracted['links'] = link_matches  # Store URLs for deduplication
        extracted['link_count_markdown'] = len(link_matches)
        
        # Count headings (markdown headings: # ## ###)
        heading_pattern = r'^#{1,6}\s+'
        headings = re.findall(heading_pattern, markdown, re.MULTILINE)
        extracted['heading_count'] = len(headings)
        
        return extracted
    
    def extract_section_data(self,
                            section_name: str,
                            api_data: Optional[Dict[str, Any]],
                            markdown: str,
                            platform: str) -> Dict[str, Any]:
        """
        Extract section-specific data using rule-based methods
        
        Args:
            section_name: Name of the section
            api_data: API JSON data
            markdown: Markdown content
            platform: 'amber' or 'uhomes'
            
        Returns:
            Dictionary with rule-based extracted data for this section
        """
        section_data = {
            'section_name': section_name,
            'rule_based_counts': {}
        }
        
        # Extract from API data first (most accurate)
        if api_data:
            api_extracted = self._extract_section_from_api(section_name, api_data, platform)
            section_data['rule_based_counts'].update(api_extracted)
        
        # Extract from markdown as supplement
        markdown_extracted = self._extract_section_from_markdown(section_name, markdown)
        section_data['rule_based_counts'].update(markdown_extracted)
        
        return section_data
    
    def _extract_amber_api(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from Amber API response"""
        extracted = {}
        
        data = api_data.get('data', {})
        meta = data.get('meta', {})
        
        # Images
        images = data.get('images', [])
        extracted['images'] = images if isinstance(images, list) else []
        extracted['image_count'] = len(extracted['images'])
        # Extract image URLs from all possible fields
        image_urls = []
        for img in extracted['images']:
            url = img.get('url') or img.get('path') or img.get('base_path', '')
            if url:
                image_urls.append(url)
        extracted['image_urls'] = image_urls
        
        # Videos
        videos = data.get('videos', [])
        if isinstance(videos, list):
            extracted['videos'] = videos
            extracted['video_count'] = len(videos)
            extracted['video_urls'] = [v.get('path', '') for v in videos if v.get('path')]
            extracted['video_types'] = list(set([v.get('type', '') for v in videos if v.get('type')]))
            extracted['has_video_tour'] = len(videos) > 0
            extracted['total_videos_count'] = meta.get('total_videos_count', len(videos))
        else:
            extracted['videos'] = []
            extracted['video_count'] = 0
            extracted['has_video_tour'] = False
        
        # Virtual Tours (360°/3D)
        virtual_views = data.get('virtual_views', [])
        if isinstance(virtual_views, list):
            extracted['virtual_tours'] = virtual_views
            extracted['virtual_tour_count'] = len(virtual_views)
            extracted['virtual_tour_urls'] = [vt.get('id', '') for vt in virtual_views if vt.get('id')]
            extracted['has_360_tour'] = any('virtual' in vt.get('type', '').lower() or '360' in vt.get('type', '').lower() or 'vr' in vt.get('type', '').lower() for vt in virtual_views)
            extracted['has_3d_tour'] = any('3d' in vt.get('type', '').lower() or '3-d' in vt.get('type', '').lower() for vt in virtual_views)
            extracted['total_virtual_views_count'] = meta.get('total_virtual_views_count', len(virtual_views))
        else:
            extracted['virtual_tours'] = []
            extracted['virtual_tour_count'] = 0
            extracted['has_360_tour'] = False
            extracted['has_3d_tour'] = False
        
        # Hero Section Features
        extracted['has_map'] = meta.get('is_map_view_enabled', False)
        extracted['has_map_toggle'] = meta.get('is_map_view_enabled', False)  # Assume toggle if map exists
        extracted['has_price_display'] = bool(data.get('pricing', {}))
        
        # Links (extract from description HTML)
        import re
        from html.parser import HTMLParser
        
        class LinkExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    for attr_name, attr_value in attrs:
                        if attr_name == 'href' and attr_value:
                            self.links.append(attr_value)
        
        descriptions = data.get('description', [])
        all_links = []
        for desc in descriptions:
            desc_value = desc.get('value', '')
            if desc_value:
                extractor = LinkExtractor()
                try:
                    extractor.feed(desc_value)
                    all_links.extend(extractor.links)
                except:
                    pass
        extracted['links'] = list(set(all_links))
        extracted['link_count'] = len(extracted['links'])
        
        # Features/Amenities
        features = data.get('features', [])
        if isinstance(features, list):
            amenities = []
            amenity_categories = {}
            for feature_group in features:
                group_name = feature_group.get('name', 'Uncategorized')
                group_values = feature_group.get('values', [])
                if isinstance(group_values, list):
                    group_amenities = [v.get('name', '') for v in group_values if v.get('name')]
                    amenities.extend(group_amenities)
                    if group_amenities:
                        amenity_categories[group_name] = group_amenities
            
            extracted['amenities'] = amenities
            extracted['amenity_count'] = len(amenities)
            extracted['amenity_categories'] = amenity_categories
            extracted['amenity_category_count'] = len(amenity_categories)
        
        # FAQs
        faqs = data.get('faqs', [])
        if isinstance(faqs, list):
            extracted['faqs'] = faqs
            extracted['faq_count'] = len(faqs)
            extracted['faq_questions'] = [f.get('question', '') for f in faqs if f.get('question')]
            extracted['faq_topics'] = list(set([f.get('category', 'General') for f in faqs if f.get('category')]))
        
        # Room Types
        room_types = data.get('room_types', [])
        if isinstance(room_types, list):
            extracted['room_types'] = room_types
            extracted['room_type_count'] = len(room_types)
            extracted['room_type_names'] = [r.get('name', '') for r in room_types if r.get('name')]
            extracted['has_room_prices'] = any(r.get('price') for r in room_types)
            extracted['has_room_sizes'] = any(r.get('size') or r.get('dimensions') for r in room_types)
        
        # Offers (from offers array + cro_tags)
        offers = data.get('offers', [])
        cro_tags = meta.get('cro_tags', {})
        
        # Combine offers from array and cro_tags
        all_offers = []
        if isinstance(offers, list):
            all_offers.extend(offers)
        
        # Add cashback offer
        if cro_tags.get('cashback'):
            all_offers.append({
                'name': 'Cashback',
                'description': f"£{cro_tags.get('cashback')} cashback",
                'amount': cro_tags.get('cashback'),
                'type': 'cashback'
            })
        
        # Add amber_sale offer
        amber_sale = cro_tags.get('amber_sale', {})
        if amber_sale.get('status') == 'true' and amber_sale.get('offer'):
            all_offers.append({
                'name': 'Amber Sale',
                'description': amber_sale.get('offer'),
                'type': 'amber_sale',
                'status': amber_sale.get('status')
            })
        
        extracted['offers'] = all_offers
        extracted['offer_count'] = len(all_offers)
        extracted['offer_names'] = [o.get('name', '') for o in all_offers if o.get('name')]
        extracted['offer_types'] = list(set([o.get('type', 'general') for o in all_offers if o.get('type')]))
        
        # Payment Details
        payment_details = {
            'installment_options': [],
            'payment_methods': [],
            'guarantor_required': False,
            'holding_fee': None,
            'deposit': None
        }
        
        for desc in descriptions:
            tag = desc.get('tag', '')
            value = desc.get('value', '')
            short_text = desc.get('short_text', '')
            
            if tag == 'payment_instalment_plan':
                installment_option = desc.get('payment_installment_option', [])
                if installment_option:
                    payment_details['installment_options'] = installment_option
                elif '1, 2, 4' in short_text or '1, 2, 4' in value:
                    payment_details['installment_options'] = [1, 2, 4]
            
            if tag == 'mode_of_payment':
                if 'credit' in value.lower() or 'debit' in value.lower():
                    payment_details['payment_methods'].append('Credit/Debit Card')
                if 'bank transfer' in value.lower():
                    payment_details['payment_methods'].append('Bank Transfer')
                if 'phone' in value.lower():
                    payment_details['payment_methods'].append('Phone Payment')
            
            if tag == 'guarantor_requirement':
                payment_details['guarantor_required'] = True
            
            if tag == 'fully_refundable_holding_fee':
                fee_match = re.search(r'£(\d+)', value)
                if fee_match:
                    payment_details['holding_fee'] = {
                        'amount': int(fee_match.group(1)),
                        'currency': 'GBP',
                        'refundable': 'refundable' in value.lower()
                    }
        
        # Extract deposit from pricing
        pricing = data.get('pricing', {})
        if isinstance(pricing, dict):
            extracted['pricing'] = pricing
            extracted['has_pricing'] = bool(pricing.get('min_price') or pricing.get('max_price'))
            extracted['has_deposit'] = bool(pricing.get('deposit'))
            if pricing.get('deposit'):
                payment_details['deposit'] = {
                    'amount': pricing.get('deposit'),
                    'currency': '£' if pricing.get('currency') == 'pound' else '$'
                }
        
        extracted['payment_details'] = payment_details
        
        # Descriptions
        if isinstance(descriptions, list):
            about_desc = next((d.get('value', '') for d in descriptions if d.get('name') == 'about'), '')
            if about_desc:
                extracted['about_property'] = about_desc
                extracted['about_word_count'] = len(about_desc.split())
        
        # Nearby Properties (if available)
        nearby_properties = data.get('nearby_properties', [])
        if not nearby_properties:
            nearby_properties = meta.get('similar_properties', [])
        extracted['nearby_properties'] = nearby_properties if isinstance(nearby_properties, list) else []
        extracted['nearby_property_count'] = len(extracted['nearby_properties'])
        
        # Property Highlights
        highlights = data.get('highlights', [])
        extracted['highlights'] = highlights if isinstance(highlights, list) else []
        extracted['highlight_count'] = len(extracted['highlights'])
        
        # Tags
        tags = data.get('tags', [])
        extracted['tags'] = tags if isinstance(tags, list) else []
        extracted['tag_count'] = len(extracted['tags'])
        
        # Owner Contact
        owner = data.get('owner', {})
        extracted['owner'] = owner
        extracted['owner_emails'] = owner.get('emails', []) if isinstance(owner, dict) else []
        extracted['owner_phones'] = owner.get('phones', []) if isinstance(owner, dict) else []
        
        # Location Details
        location = data.get('location', {})
        extracted['location'] = location
        extracted['location_coordinates'] = data.get('location_coordinates', '')
        if isinstance(location, dict):
            extracted['full_address'] = location.get('primary', '') or location.get('name', '')
            extracted['postal_code'] = location.get('postal_code', {}).get('long_name', '') if isinstance(location.get('postal_code'), dict) else ''
            extracted['city'] = location.get('locality', {}).get('long_name', '') if isinstance(location.get('locality'), dict) else ''
            extracted['coordinates'] = location.get('location_coordinates', {})
        
        # Payment Types
        payment_types = data.get('payment_types', [])
        extracted['payment_types'] = payment_types if isinstance(payment_types, list) else []
        
        # Weekly Price
        extracted['weekly_price'] = data.get('weekly_price')
        
        # Property Info Tags
        property_info_tags = meta.get('property_info_tags', [])
        extracted['property_info_tags'] = property_info_tags if isinstance(property_info_tags, list) else []
        # Extract specific values
        for tag in property_info_tags:
            if isinstance(tag, dict):
                tag_type = tag.get('type', '')
                tag_value = tag.get('value', '')
                if tag_type == 'total_units':
                    extracted['unit_count'] = tag_value
                elif tag_type == 'highest_floor':
                    extracted['highest_floor'] = tag_value
                elif tag_type == 'build_in_year':
                    extracted['build_year'] = tag_value
        
        # Unit Types (from meta)
        unit_types = meta.get('unit_types', [])
        extracted['unit_types'] = unit_types if isinstance(unit_types, list) else []
        
        # Area Information
        extracted['max_area'] = meta.get('max_area')
        extracted['min_area'] = meta.get('min_area')
        extracted['area_unit'] = meta.get('area_unit', 'sqm')
        
        # Amenity Prices
        amenity_prices = meta.get('amenity_prices', {})
        extracted['amenity_prices'] = amenity_prices if isinstance(amenity_prices, dict) else {}
        
        # Facts (Community Facts)
        facts = meta.get('facts', [])
        extracted['facts'] = facts if isinstance(facts, list) else []
        extracted['fact_count'] = len(extracted['facts'])
        
        # Additional Meta Fields
        extracted['floor'] = meta.get('floor')
        extracted['facing'] = meta.get('facing')
        extracted['types'] = meta.get('types', [])
        extracted['guarantor_required'] = meta.get('guarantor_required')
        extracted['year_of_construction'] = meta.get('year_of_construction')
        extracted['lease_duration_unit'] = meta.get('lease_duration_unit')
        
        return extracted
    
    def _extract_uhomes_api(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from UHomes API response"""
        extracted = {}
        
        switch = api_data.get('switch', {})
        house = api_data.get('house', {})
        location = api_data.get('location', {})
        tips = api_data.get('tips', {})
        
        # Images (from media array and media.images)
        all_images = []
        
        # Extract from media array (type: "image")
        media_array = api_data.get('media', [])
        for media_item in media_array:
            if media_item.get('type') == 'image' and media_item.get('items'):
                for img_item in media_item.get('items', []):
                    media_img = img_item.get('media_img', {})
                    if media_img.get('path'):
                        all_images.append(media_img)
        
        # Also check media.images for backward compatibility
        media = api_data.get('media', {})
        if isinstance(media, dict):
            images = media.get('images', [])
            if isinstance(images, list):
                all_images.extend(images)
        
        extracted['images'] = all_images
        extracted['image_count'] = len(all_images)
        # Extract image URLs from all possible fields
        image_urls = []
        for img in all_images:
            if isinstance(img, dict):
                url = img.get('url') or img.get('src') or img.get('path', '')
                if url:
                    image_urls.append(url)
        extracted['image_urls'] = image_urls
        
        # Videos (from multiple sources)
        digital_videos = tips.get('digital_human_videos', {})
        videos = []
        if digital_videos and digital_videos.get('items'):
            videos.extend(digital_videos.get('items', []))
        
        # Extract from media array
        media_array = api_data.get('media', [])
        for media_item in media_array:
            if media_item.get('type') == 'video' and media_item.get('items'):
                videos.extend(media_item.get('items', []))
        
        # Extract from room types
        room_types_data = api_data.get('room_types', {})
        room_type_items = room_types_data.get('room_type_items', [])
        for room_item in room_type_items:
            media = room_item.get('media', {})
            video_items = media.get('video', [])
            if video_items:
                videos.extend(video_items)
        
        extracted['videos'] = videos
        extracted['video_count'] = len(videos)
        extracted['video_urls'] = [v.get('video_url', '') or (v.get('media_video', {}) or {}).get('video_url', '') for v in videos if v.get('video_url') or (v.get('media_video', {}) or {}).get('video_url')]
        extracted['has_video_tour'] = bool(switch.get('is_has_video', 0)) or len(videos) > 0
        extracted['has_live_video_tour'] = bool(switch.get('is_live_video_tour', 0))
        extracted['on_site_video'] = bool(switch.get('on_site_video', 0))
        
        # Virtual Tours (360°/VR) from room types
        has_360_tour = False
        vr_link_count = 0
        for room_item in room_type_items:
            media = room_item.get('media', {})
            media_meta = media.get('meta', {})
            if media_meta.get('vr_link_count', 0) > 0:
                has_360_tour = True
                vr_link_count += media_meta.get('vr_link_count', 0)
        
        extracted['has_360_tour'] = has_360_tour
        extracted['vr_link_count'] = vr_link_count
        
        # Hero Section Features
        extracted['has_map'] = bool(house.get('staticmap_image'))
        extracted['has_map_toggle'] = bool(house.get('staticmap_image'))
        extracted['has_street_view'] = bool(location.get('street_view_lat') and location.get('street_view_lng'))
        extracted['has_price_display'] = bool(house.get('rent_amount'))
        
        # Links (extract from about text HTML)
        from html.parser import HTMLParser
        
        class LinkExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    for attr_name, attr_value in attrs:
                        if attr_name == 'href' and attr_value:
                            self.links.append(attr_value)
        
        about = api_data.get('about', {})
        all_links = []
        if isinstance(about, dict):
            about_text = about.get('text', '')
            if about_text:
                extractor = LinkExtractor()
                try:
                    extractor.feed(about_text)
                    all_links = extractor.links
                except:
                    pass
        extracted['links'] = list(set(all_links))
        extracted['link_count'] = len(extracted['links'])
        
        # Features/Amenities
        features = api_data.get('features', [])
        if isinstance(features, list):
            # ALL amenities (no filter)
            all_amenities = []
            seen_all = set()  # Track duplicates (case-insensitive)
            for feature in features:
                name = feature.get('name', '').strip()
                if name:
                    name_lower = name.lower()
                    if name_lower not in seen_all:
                        seen_all.add(name_lower)
                        all_amenities.append(name)
            
            # Property-level amenities only (exclude room-level: Kitchen/Bedroom/Bathroom/General)
            # Property-level sub_types: 11 (Safety), 55 (Property Services), 56 (Shared Community),
            # 57 (Fitness & Recreation), 58 (Outdoor Features)
            property_level_subtypes = [11, 55, 56, 57, 58]
            amenities = []
            seen_names = set()  # Track duplicates (case-insensitive)
            
            for feature in features:
                sub_type = feature.get('sub_type')
                if sub_type in property_level_subtypes:
                    name = feature.get('name', '').strip()
                    if name:
                        name_lower = name.lower()
                        if name_lower not in seen_names:
                            seen_names.add(name_lower)
                            amenities.append(name)
            
            # Store both property-level and all amenities
            extracted['amenities'] = amenities
            extracted['amenity_count'] = len(amenities)
            extracted['all_amenities'] = all_amenities
            extracted['all_amenity_count'] = len(all_amenities)
        
        # FAQs - check multiple possible locations
        faqs = []
        # Check 'faq' key first
        if api_data.get('faq'):
            faqs = api_data.get('faq', [])
        # Check 'features_faq' if 'faq' is empty
        elif api_data.get('features_faq'):
            faqs = api_data.get('features_faq', [])
        
        if isinstance(faqs, list) and len(faqs) > 0:
            extracted['faqs'] = faqs
            extracted['faq_count'] = len(faqs)
            extracted['faq_questions'] = [
                f.get('question') or f.get('title', '') 
                for f in faqs 
                if f.get('question') or f.get('title')
            ]
        else:
            extracted['faqs'] = []
            extracted['faq_count'] = 0
            extracted['faq_questions'] = []
        
        # Offers (from promotion + media_bottom)
        promotions = api_data.get('promotion', [])
        media_bottom = tips.get('media_bottom', [])
        
        all_offers = []
        if isinstance(promotions, list):
            all_offers.extend(promotions)
        
        for offer in media_bottom:
            offer_amount = offer.get('offer_amount', {})
            all_offers.append({
                'name': offer.get('desc', 'Exclusive Offer'),
                'description': f"Up to {offer_amount.get('abbr', '£')}{offer_amount.get('amount', '')}",
                'type': offer.get('type', 'exclusive_offer')
            })
        
        extracted['offers'] = all_offers
        extracted['offer_count'] = len(all_offers)
        extracted['offer_names'] = [o.get('title') or o.get('name', '') for o in all_offers if o.get('title') or o.get('name')]
        
        # Payment Details
        fees = api_data.get('fees', {})
        installment_data = api_data.get('installment', [])
        
        payment_details = {
            'installment_options': [],
            'payment_methods': [],
            'guarantor_required': False,
            'deposit': None,
            'other_fees': []
        }
        
        # Extract installment options
        if installment_data:
            for inst in installment_data:
                inst_count = inst.get('installment_count', 0)
                if inst_count > 0 and inst_count not in payment_details['installment_options']:
                    payment_details['installment_options'].append(inst_count)
                if inst.get('guarantor', 0) > 0:
                    payment_details['guarantor_required'] = True
        
        if house.get('installment_count', 0) > 0:
            if house.get('installment_count') not in payment_details['installment_options']:
                payment_details['installment_options'].append(house.get('installment_count'))
        
        # Check cancellation/refund policy text for guarantor mentions (if not already found)
        if not payment_details['guarantor_required']:
            rules = api_data.get('rules', [])
            for rule in rules:
                # Check cancellation policies
                if rule.get('policy_type') == 'cancel':
                    policy_text_obj = rule.get('policy_text', {})
                    policy_text = policy_text_obj.get('text', '') if isinstance(policy_text_obj, dict) else (policy_text_obj if isinstance(policy_text_obj, str) else '')
                    if policy_text and 'guarantor' in policy_text.lower():
                        text_lower = policy_text.lower()
                        
                        # Check for negative phrases first
                        negative_phrases = ['no guarantor', 'guarantor not required', 'guarantor not needed', 
                                          'not require a guarantor', 'guarantor: not', 'guarantor not',
                                          'is not required', 'not required', 'does not require']
                        has_negative = any(phrase in text_lower for phrase in negative_phrases)
                        
                        if has_negative:
                            payment_details['guarantor_required'] = False
                            sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                            payment_details['guarantor_details'] = {
                                'source': 'cancellation_policy',
                                'text': '. '.join(sentences[:2]) if sentences else policy_text[:300],
                                'note': 'Explicitly states no guarantor required'
                            }
                            break
                        else:
                            # Check for positive phrases
                            positive_phrases = ['guarantor must', 'guarantor is required', 'guarantor required', 
                                               'must sign', 'guarantor and', 'guarantor will']
                            has_positive = any(phrase in text_lower for phrase in positive_phrases)
                            
                            if has_positive:
                                payment_details['guarantor_required'] = True
                                sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                                payment_details['guarantor_details'] = {
                                    'source': 'cancellation_policy',
                                    'text': '. '.join(sentences[:3]) if sentences else policy_text[:500],
                                    'note': 'Extracted from cancellation policy text'
                                }
                                break
                            else:
                                # Mentioned but unclear
                                payment_details['guarantor_required'] = None
                                sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                                payment_details['guarantor_details'] = {
                                    'source': 'cancellation_policy',
                                    'text': '. '.join(sentences[:2]) if sentences else policy_text[:300],
                                    'note': 'Guarantor mentioned but requirement unclear - needs review'
                                }
                                break
                
                # Check refund policies (if separate)
                if rule.get('policy_type') == 'refund':
                    policy_text_obj = rule.get('policy_text', {})
                    policy_text = policy_text_obj.get('text', '') if isinstance(policy_text_obj, dict) else (policy_text_obj if isinstance(policy_text_obj, str) else '')
                    if policy_text and 'guarantor' in policy_text.lower():
                        text_lower = policy_text.lower()
                        negative_phrases = ['no guarantor', 'guarantor not required', 'guarantor not needed']
                        positive_phrases = ['guarantor must', 'guarantor is required', 'guarantor required']
                        
                        has_negative = any(phrase in text_lower for phrase in negative_phrases)
                        has_positive = any(phrase in text_lower for phrase in positive_phrases)
                        
                        if has_negative:
                            payment_details['guarantor_required'] = False
                            break
                        elif has_positive:
                            payment_details['guarantor_required'] = True
                            sentences = [s.strip() for s in policy_text.split('.') if 'guarantor' in s.lower()]
                            payment_details['guarantor_details'] = {
                                'source': 'refund_policy',
                                'text': '. '.join(sentences[:3]) if sentences else policy_text[:500]
                            }
                            break
        
        payment_details['payment_method_ids'] = house.get('payment_method', [])
        
        # Extract deposit
        if fees.get('deposit'):
            deposit = fees['deposit'].get('amount', {})
            if deposit:
                payment_details['deposit'] = {
                    'amount': deposit.get('amount', ''),
                    'currency': deposit.get('abbr', '£')
                }
        
        # Extract other fees
        other_fees = fees.get('other_fees', [])
        for fee in other_fees:
            fee_amount = fee.get('amount', {})
            payment_details['other_fees'].append({
                'title': fee.get('title', ''),
                'amount': fee_amount.get('amount', '') if isinstance(fee_amount, dict) else '',
                'currency': fee_amount.get('abbr', '£') if isinstance(fee_amount, dict) else '£'
            })
        
        extracted['payment_details'] = payment_details
        
        # About
        if isinstance(about, dict):
            about_text = about.get('text_strip_html', '')
            if about_text:
                extracted['about_property'] = about_text
                extracted['about_word_count'] = len(about_text.split())
        
        # House/Pricing
        if isinstance(house, dict):
            rent_amount = house.get('rent_amount', {})
            if isinstance(rent_amount, dict):
                extracted['pricing'] = rent_amount
                extracted['has_pricing'] = bool(rent_amount.get('amount'))
        
        # Rules
        rules = api_data.get('rules', [])
        if isinstance(rules, list):
            extracted['property_rules'] = rules
            extracted['rule_count'] = len(rules)
        
        # Nearby
        nearby = api_data.get('nearby', [])
        if isinstance(nearby, list):
            extracted['nearby_properties'] = nearby
            extracted['nearby_count'] = len(nearby)
        
        # Nearby Properties (also check tips)
        nearby_props = api_data.get('nearby_properties', [])
        if not nearby_props:
            nearby_props = tips.get('similar_properties', [])
        extracted['nearby_properties'] = nearby_props if isinstance(nearby_props, list) else []
        extracted['nearby_property_count'] = len(extracted['nearby_properties'])
        
        # Room Types (from room_type_items)
        room_types_list = []
        for room_item in room_type_items:
            room_type = room_item.get('room_type', {})
            media = room_item.get('media', {})
            media_meta = media.get('meta', {})
            
            room_types_list.append({
                'name': room_type.get('name', ''),
                'type_id': room_type.get('type_id', ''),
                'price': room_type.get('rent_amount', {}).get('amount', ''),
                'currency': room_type.get('rent_amount', {}).get('abbr', '£'),
                'area_sqm': room_type.get('area_sqm', {}),
                'bed_count': room_type.get('bed_count', ''),
                'bathroom_count': room_type.get('bathroom_count', ''),
                'has_360_tour': media_meta.get('vr_link_count', 0) > 0,
                'image_count': media_meta.get('image_count', 0),
                'video_count': media_meta.get('video_count', 0)
            })
        
        extracted['room_types'] = room_types_list
        extracted['room_type_count'] = len(room_types_list)
        extracted['room_type_names'] = [r.get('name', '') for r in room_types_list if r.get('name')]
        extracted['has_room_prices'] = any(r.get('price') for r in room_types_list)
        extracted['has_room_sizes'] = any(r.get('area_sqm') for r in room_types_list)
        
        return extracted
    
    def _extract_section_from_api(self,
                                 section_name: str,
                                 api_data: Dict[str, Any],
                                 platform: str) -> Dict[str, Any]:
        """Extract section-specific data from API"""
        section_data = {}
        
        if section_name == 'Hero & Media':
            if platform == 'amber':
                images = api_data.get('data', {}).get('images', [])
            else:
                images = api_data.get('media', {}).get('images', [])
            section_data['image_count'] = len(images) if isinstance(images, list) else 0
            section_data['video_count'] = 0  # Would need to check video field
        
        elif section_name == 'Amenities':
            if platform == 'amber':
                features = api_data.get('data', {}).get('features', [])
                amenities = []
                for fg in features:
                    amenities.extend([v.get('name') for v in fg.get('values', []) if v.get('name')])
            else:
                # UHomes: Filter to property-level amenities only
                # Property-level sub_types: 11 (Safety), 55 (Property Services), 56 (Shared Community),
                # 57 (Fitness & Recreation), 58 (Outdoor Features)
                # Exclude: 59 (General), 60 (Kitchen), 61 (Bedroom), 62 (Bathroom)
                features = api_data.get('features', [])
                property_level_subtypes = [11, 55, 56, 57, 58]
                amenities = []
                seen_names = set()  # Track duplicates (case-insensitive)
                
                for feature in features:
                    sub_type = feature.get('sub_type')
                    if sub_type in property_level_subtypes:
                        name = feature.get('name', '').strip()
                        if name:
                            name_lower = name.lower()
                            if name_lower not in seen_names:
                                seen_names.add(name_lower)
                                amenities.append(name)
            section_data['amenity_count'] = len(amenities)
            section_data['amenities'] = amenities
        
        elif section_name == 'FAQs':
            if platform == 'amber':
                faqs = api_data.get('data', {}).get('faqs', [])
            else:
                # Check multiple possible locations for UHomes
                faqs = api_data.get('faq', [])
                if not faqs or len(faqs) == 0:
                    faqs = api_data.get('features_faq', [])
            section_data['faq_count'] = len(faqs) if isinstance(faqs, list) else 0
            section_data['faqs'] = faqs if isinstance(faqs, list) else []
        
        elif section_name == 'Room Types':
            if platform == 'amber':
                rooms = api_data.get('data', {}).get('room_types', [])
            else:
                rooms = []  # UHomes might have different structure
            section_data['room_type_count'] = len(rooms) if isinstance(rooms, list) else 0
            section_data['room_types'] = rooms if isinstance(rooms, list) else []
            section_data['has_prices'] = any(r.get('price') for r in rooms) if isinstance(rooms, list) else False
        
        elif section_name == 'Offers':
            if platform == 'amber':
                offers = api_data.get('data', {}).get('offers', [])
            else:
                offers = api_data.get('promotion', [])
            section_data['offer_count'] = len(offers) if isinstance(offers, list) else 0
            section_data['offers'] = offers if isinstance(offers, list) else []
        
        elif section_name == 'About Property':
            if platform == 'amber':
                descriptions = api_data.get('data', {}).get('description', [])
                about = next((d.get('value', '') for d in descriptions if d.get('name') == 'about'), '')
            else:
                about = api_data.get('about', {}).get('text_strip_html', '')
            section_data['word_count'] = len(about.split()) if about else 0
            section_data['has_content'] = bool(about)
        
        return section_data
    
    def _extract_section_from_markdown(self,
                                      section_name: str,
                                      markdown: str) -> Dict[str, Any]:
        """Extract section-specific data from markdown using patterns"""
        section_data = {}
        
        # Extract section content first
        section_content = self._get_section_content(markdown, section_name)
        
        if not section_content:
            return section_data
        
        # Word count
        section_data['word_count'] = len(section_content.split())
        
        # Image count (markdown images)
        image_pattern = r'!\[.*?\]\(.*?\)'
        images = re.findall(image_pattern, section_content)
        section_data['image_count'] = len(images)
        
        # Link count
        link_pattern = r'\[.*?\]\(https?://.*?\)'
        links = re.findall(link_pattern, section_content)
        section_data['link_count'] = len(links)
        
        # Section-specific extractions
        if section_name == 'Amenities':
            # Look for list items (markdown lists: - item or * item)
            list_pattern = r'^[-*]\s+(.+)$'
            list_items = re.findall(list_pattern, section_content, re.MULTILINE)
            section_data['amenity_count'] = len(list_items)
            section_data['amenities'] = [item.strip() for item in list_items]
        
        elif section_name == 'FAQs':
            # Look for Q: or Question: patterns
            q_pattern = r'(?:Q:|Question:)\s*(.+?)(?:\n|$)'
            questions = re.findall(q_pattern, section_content, re.IGNORECASE | re.MULTILINE)
            section_data['faq_count'] = len(questions)
            section_data['faqs'] = [q.strip() for q in questions]
        
        elif section_name == 'Room Types':
            # Look for room type mentions
            room_pattern = r'\b(?:Studio|Ensuite|1BR|2BR|3BR|Single|Double|Twin|Apartment)\b'
            rooms = re.findall(room_pattern, section_content, re.IGNORECASE)
            section_data['room_type_count'] = len(set(rooms))
            section_data['room_types'] = list(set(rooms))
        
        elif section_name == 'University Links':
            # Look for distance patterns
            distance_pattern = r'[\d.]+\s*(?:mi|km|miles|kilometers)'
            distances = re.findall(distance_pattern, section_content, re.IGNORECASE)
            section_data['has_distances'] = len(distances) > 0
            section_data['distance_count'] = len(distances)
        
        return section_data
    
    def _get_section_content(self, markdown: str, section_name: str) -> str:
        """Extract section content from markdown"""
        # Map section names to patterns
        patterns = {
            'Hero & Media': [r'#\s*(?:Overview|Photos|Videos|Media)', r'^#\s+.+$'],
            'Amenities': [r'#\s*(?:Amenities|Facilities|Features)'],
            'FAQs': [r'#\s*(?:FAQs|FAQ|Questions)'],
            'Room Types': [r'#\s*(?:Room Types|Accommodation)'],
            'Offers': [r'#\s*(?:Offers|Promotions|Deals)'],
            'About Property': [r'#\s*(?:About|Description)'],
            'University Links': [r'#\s*(?:Universities|Location)']
        }
        
        section_patterns = patterns.get(section_name, [])
        
        for pattern in section_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.start()
                # Find next section or end
                next_section = re.search(r'\n#\s+', markdown[start + 100:])
                end = start + 100 + (next_section.start() if next_section else len(markdown) - start)
                return markdown[start:end]
        
        return ""
    
    def merge_extractions(self,
                         api_extracted: Dict[str, Any],
                         markdown_extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart merge of API and markdown extractions with deduplication
        
        Strategy:
        1. Use API data as primary source (more accurate, structured)
        2. Add Firecrawl/markdown data that's missing from API
        3. Deduplicate intelligently (images by URL, amenities by name, etc.)
        4. Calculate accurate counts from merged unique items
        
        Args:
            api_extracted: Data extracted from API
            markdown_extracted: Data extracted from markdown
            
        Returns:
            Merged extraction with deduplicated, complete data
        """
        merged = {}
        
        # 1. Merge Images (deduplicate by URL)
        api_images = api_extracted.get('images', [])
        markdown_images = markdown_extracted.get('images', []) or []
        
        # Extract URLs from markdown images (format: ![alt](url))
        if isinstance(markdown_images, list):
            markdown_image_urls = []
            for img in markdown_images:
                if isinstance(img, str):
                    # Extract URL from markdown image syntax
                    url_match = re.search(r'\(([^)]+)\)', img)
                    if url_match:
                        markdown_image_urls.append(url_match.group(1))
                else:
                    markdown_image_urls.append(str(img))
        else:
            markdown_image_urls = []
        
        # Normalize API image URLs (handle both strings and dicts)
        api_image_urls = []
        for img in api_images:
            if isinstance(img, dict):
                url = img.get('url') or img.get('src') or img.get('image_url', '')
            else:
                url = str(img)
            if url:
                api_image_urls.append(url)
        
        # Merge and deduplicate images
        all_image_urls = list(set(api_image_urls + markdown_image_urls))
        merged['images'] = all_image_urls
        merged['image_count'] = len(all_image_urls)
        merged['api_image_count'] = len(api_image_urls)
        merged['markdown_image_count'] = len(markdown_image_urls)
        merged['unique_image_count'] = len(all_image_urls)
        
        # 2. Merge Amenities (deduplicate by name, case-insensitive)
        api_amenities = api_extracted.get('amenities', [])
        markdown_amenities = markdown_extracted.get('amenities', []) or []
        
        # Normalize to list of strings
        api_amenity_names = [str(a).strip().lower() for a in api_amenities if a]
        markdown_amenity_names = [str(a).strip().lower() for a in markdown_amenities if a]
        
        # Merge and deduplicate (preserve original case from API first, then markdown)
        amenity_map = {}
        for a in api_amenities:
            if a:
                key = str(a).strip().lower()
                amenity_map[key] = str(a).strip()  # Use API version
        
        for a in markdown_amenities:
            if a:
                key = str(a).strip().lower()
                if key not in amenity_map:  # Only add if not in API
                    amenity_map[key] = str(a).strip()  # Use markdown version
        
        merged['amenities'] = list(amenity_map.values())
        merged['amenity_count'] = len(merged['amenities'])
        merged['api_amenity_count'] = len(api_amenities)
        merged['markdown_amenity_count'] = len(markdown_amenities)
        merged['unique_amenity_count'] = len(merged['amenities'])
        
        # Preserve amenity categories from API (if available)
        if 'amenity_categories' in api_extracted:
            merged['amenity_categories'] = api_extracted['amenity_categories']
        
        # 3. Merge FAQs (deduplicate by question, case-insensitive)
        api_faqs = api_extracted.get('faqs', [])
        markdown_faqs = markdown_extracted.get('faqs', []) or []
        
        # Normalize FAQs
        faq_map = {}
        for faq in api_faqs:
            if isinstance(faq, dict):
                question = faq.get('question') or faq.get('title', '')
            else:
                question = str(faq)
            if question:
                key = question.strip().lower()
                faq_map[key] = faq if isinstance(faq, dict) else {'question': question}
        
        for faq in markdown_faqs:
            if isinstance(faq, dict):
                question = faq.get('question') or faq.get('title', '')
            else:
                question = str(faq)
            if question:
                key = question.strip().lower()
                if key not in faq_map:  # Only add if not in API
                    faq_map[key] = faq if isinstance(faq, dict) else {'question': question}
        
        merged['faqs'] = list(faq_map.values())
        merged['faq_count'] = len(merged['faqs'])
        merged['api_faq_count'] = len(api_faqs)
        merged['markdown_faq_count'] = len(markdown_faqs)
        merged['unique_faq_count'] = len(merged['faqs'])
        
        # 4. Merge Room Types (deduplicate by name, case-insensitive)
        api_rooms = api_extracted.get('room_types', [])
        markdown_rooms = markdown_extracted.get('room_types', []) or []
        
        room_map = {}
        for room in api_rooms:
            if isinstance(room, dict):
                name = room.get('name', '')
            else:
                name = str(room)
            if name:
                key = name.strip().lower()
                room_map[key] = room if isinstance(room, dict) else {'name': name}
        
        for room in markdown_rooms:
            if isinstance(room, dict):
                name = room.get('name', '')
            else:
                name = str(room)
            if name:
                key = name.strip().lower()
                if key not in room_map:  # Only add if not in API
                    room_map[key] = room if isinstance(room, dict) else {'name': name}
        
        merged['room_types'] = list(room_map.values())
        merged['room_type_count'] = len(merged['room_types'])
        merged['api_room_count'] = len(api_rooms)
        merged['markdown_room_count'] = len(markdown_rooms)
        merged['unique_room_count'] = len(merged['room_types'])
        
        # 5. Merge Offers (deduplicate by name/title, case-insensitive)
        api_offers = api_extracted.get('offers', [])
        markdown_offers = markdown_extracted.get('offers', []) or []
        
        offer_map = {}
        for offer in api_offers:
            if isinstance(offer, dict):
                name = offer.get('name') or offer.get('title', '')
            else:
                name = str(offer)
            if name:
                key = name.strip().lower()
                offer_map[key] = offer if isinstance(offer, dict) else {'name': name}
        
        for offer in markdown_offers:
            if isinstance(offer, dict):
                name = offer.get('name') or offer.get('title', '')
            else:
                name = str(offer)
            if name:
                key = name.strip().lower()
                if key not in offer_map:  # Only add if not in API
                    offer_map[key] = offer if isinstance(offer, dict) else {'name': name}
        
        merged['offers'] = list(offer_map.values())
        merged['offer_count'] = len(merged['offers'])
        merged['api_offer_count'] = len(api_offers)
        merged['markdown_offer_count'] = len(markdown_offers)
        merged['unique_offer_count'] = len(merged['offers'])
        
        # 6. Merge Links (deduplicate by URL)
        api_links = api_extracted.get('links', []) or []
        markdown_links = markdown_extracted.get('links', []) or markdown_extracted.get('link_count_markdown', 0)
        
        # Extract URLs from markdown links
        if isinstance(markdown_links, list):
            markdown_link_urls = [str(link) for link in markdown_links]
        else:
            markdown_link_urls = []
        
        api_link_urls = [str(link) for link in api_links]
        all_link_urls = list(set(api_link_urls + markdown_link_urls))
        merged['links'] = all_link_urls
        merged['link_count'] = len(all_link_urls)
        
        # 7. Merge other fields (prefer API, fill gaps with markdown)
        # Word count: use markdown (more accurate for text content)
        merged['word_count'] = markdown_extracted.get('word_count', 0) or api_extracted.get('word_count', 0)
        
        # Video count: prefer API
        merged['video_count'] = api_extracted.get('video_count', 0) or markdown_extracted.get('video_count', 0)
        
        # Property rules: merge lists
        api_rules = api_extracted.get('property_rules', []) or []
        markdown_rules = markdown_extracted.get('property_rules', []) or []
        rule_map = {str(r).strip().lower(): str(r).strip() for r in api_rules}
        for r in markdown_rules:
            key = str(r).strip().lower()
            if key not in rule_map:
                rule_map[key] = str(r).strip()
        merged['property_rules'] = list(rule_map.values())
        
        # Pricing: prefer API (more structured)
        if 'pricing' in api_extracted:
            merged['pricing'] = api_extracted['pricing']
            merged['has_pricing'] = api_extracted.get('has_pricing', False)
        elif 'pricing' in markdown_extracted:
            merged['pricing'] = markdown_extracted['pricing']
            merged['has_pricing'] = markdown_extracted.get('has_pricing', False)
        
        # About property: prefer longer/more detailed version
        api_about = api_extracted.get('about_property', '')
        markdown_about = markdown_extracted.get('about_property', '')
        if len(markdown_about) > len(api_about):
            merged['about_property'] = markdown_about
        else:
            merged['about_property'] = api_about or markdown_about
        
        # Copy other API fields (prefer API for structured data)
        for key, value in api_extracted.items():
            if key not in merged and value:
                merged[key] = value
        
        # Fill remaining gaps with markdown data
        for key, value in markdown_extracted.items():
            if key not in merged and value:
                merged[key] = value
        
        # Mark data sources and merge statistics
        merged['has_api_data'] = bool(api_extracted.get('image_count') or api_extracted.get('amenity_count'))
        merged['has_markdown_data'] = bool(markdown_extracted.get('word_count') or markdown_extracted.get('image_count'))
        merged['merge_stats'] = {
            'images_added_from_markdown': len(markdown_image_urls) - len(set(api_image_urls) & set(markdown_image_urls)),
            'amenities_added_from_markdown': len(markdown_amenity_names) - len(set(api_amenity_names) & set(markdown_amenity_names)),
            'faqs_added_from_markdown': len(markdown_faqs) - len(set([str(f).lower() for f in api_faqs]) & set([str(f).lower() for f in markdown_faqs])),
            'total_unique_items': merged['unique_image_count'] + merged['unique_amenity_count'] + merged['unique_faq_count']
        }
        
        return merged


if __name__ == "__main__":
    # Test extractor
    extractor = RuleBasedExtractor()
    
    # Test API extraction
    amber_api = {
        'data': {
            'images': ['img1.jpg', 'img2.jpg'],
            'features': [
                {'name': 'Common', 'values': [{'name': 'WiFi'}, {'name': 'Heating'}]}
            ],
            'faqs': [{'question': 'Q1', 'answer': 'A1'}],
            'room_types': [{'name': 'Studio', 'price': 100}]
        }
    }
    
    extracted = extractor.extract_from_api_data(amber_api, 'amber')
    print(f"Extracted: {json.dumps(extracted, indent=2)}")

