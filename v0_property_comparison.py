"""
V0 Property Comparison Tool
Simple property-level comparison between Amber and UHomes

This is a V0 tool - simple, focused, and easy to understand.
Shows property-level differences without complex scoring.
"""

import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.sheets_manager import SheetsManager
from src.utils.logger import setup_logger

logger = setup_logger("V0Comparison")


class V0PropertyComparison:
    """
    V0 Property Comparison Tool
    
    Compares properties at property level:
    - Shows what each platform has
    - Highlights key differences
    - Simple metrics comparison
    """
    
    def __init__(self):
        self.sheets = SheetsManager()
        logger.info("✅ V0 Property Comparison initialized")
    
    def compare_property(self, property_id: str) -> Dict[str, Any]:
        """
        Compare a single property between Amber and UHomes
        
        Args:
            property_id: Property ID (e.g., 'P001')
            
        Returns:
            Comparison dictionary
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Comparing Property: {property_id}")
        logger.info(f"{'='*80}")
        
        try:
            # Read extracted content
            content_df = self.sheets.read_sheet('Content_Extraction')
            property_content = content_df[content_df['Property_ID'] == property_id]
            
            if len(property_content) == 0:
                logger.error(f"No content found for {property_id}")
                return {'error': 'No content found'}
            
            # Get property name
            property_name = property_content.iloc[0]['Property_Name']
            
            # Separate by platform
            amber_content = property_content[property_content['Platform'] == 'amber']
            uhomes_content = property_content[property_content['Platform'] == 'uhomes']
            
            if len(amber_content) == 0 or len(uhomes_content) == 0:
                logger.error(f"Missing platform data for {property_id}")
                return {'error': 'Missing platform data'}
            
            # Build comparison
            comparison = {
                'property_id': property_id,
                'property_name': property_name,
                'compared_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sections': {}
            }
            
            # Compare each section
            section_names = [
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
            
            for section_name in section_names:
                amber_section = amber_content[amber_content['Section_Name'] == section_name]
                uhomes_section = uhomes_content[uhomes_content['Section_Name'] == section_name]
                
                section_comparison = self._compare_section(
                    section_name, amber_section, uhomes_section
                )
                comparison['sections'][section_name] = section_comparison
            
            # Calculate summary metrics
            comparison['summary'] = self._calculate_summary(comparison['sections'])
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing {property_id}: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
    
    def _compare_section(self, section_name: str, 
                        amber_section: pd.DataFrame,
                        uhomes_section: pd.DataFrame) -> Dict[str, Any]:
        """Compare a single section between platforms"""
        
        # Get data
        amber_data = {}
        uhomes_data = {}
        
        if len(amber_section) > 0:
            amber_row = amber_section.iloc[0]
            amber_json = amber_row.get('Content_JSON', '{}')
            try:
                amber_data = json.loads(amber_json) if amber_json else {}
            except:
                amber_data = {}
        
        if len(uhomes_section) > 0:
            uhomes_row = uhomes_section.iloc[0]
            uhomes_json = uhomes_row.get('Content_JSON', '{}')
            try:
                uhomes_data = json.loads(uhomes_json) if uhomes_json else {}
            except:
                uhomes_data = {}
        
        # Extract key metrics based on section
        comparison = {
            'section': section_name,
            'amber': {},
            'uhomes': {},
            'differences': [],
            'improvement_needed': [],  # Where UHomes does better (Amber needs to improve)
            'uhomes_better_count': 0  # Count of metrics where UHomes is better
        }
        
        if section_name == 'Hero & Media':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'image_count': amber_data.get('image_count', 0),
                'video_count': amber_data.get('video_count', 0),  # Total videos (includes video tours)
                'virtual_tour_count': amber_data.get('virtual_tour_count', 0),  # Total virtual tours (includes 360° and 3D)
                'live_count': amber_data.get('live_count', 0),
                'by_tenant_count': amber_data.get('by_tenant_count', 0),
                'has_map': amber_data.get('has_map', False)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'image_count': uhomes_data.get('image_count', 0),
                'video_count': uhomes_data.get('video_count', 0),  # Total videos (includes video tours)
                'virtual_tour_count': uhomes_data.get('virtual_tour_count', 0),  # Total virtual tours (includes 360° and 3D)
                'live_count': uhomes_data.get('live_count', 0),
                'by_tenant_count': uhomes_data.get('by_tenant_count', 0),
                'has_map': uhomes_data.get('has_map', False)
            }
            
            # Find differences and track improvement needed
            if comparison['amber']['image_count'] != comparison['uhomes']['image_count']:
                comparison['differences'].append(
                    f"Images: Amber has {comparison['amber']['image_count']}, "
                    f"UHomes has {comparison['uhomes']['image_count']}"
                )
                if comparison['uhomes']['image_count'] > comparison['amber']['image_count']:
                    comparison['improvement_needed'].append('Images')
                    comparison['uhomes_better_count'] += 1
            
            if comparison['amber']['video_count'] != comparison['uhomes']['video_count']:
                comparison['differences'].append(
                    f"Videos: Amber has {comparison['amber']['video_count']}, "
                    f"UHomes has {comparison['uhomes']['video_count']}"
                )
                if comparison['uhomes']['video_count'] > comparison['amber']['video_count']:
                    comparison['improvement_needed'].append('Videos')
                    comparison['uhomes_better_count'] += 1
            
            if comparison['amber']['virtual_tour_count'] != comparison['uhomes']['virtual_tour_count']:
                comparison['differences'].append(
                    f"Virtual Tours: Amber has {comparison['amber']['virtual_tour_count']}, "
                    f"UHomes has {comparison['uhomes']['virtual_tour_count']}"
                )
                if comparison['uhomes']['virtual_tour_count'] > comparison['amber']['virtual_tour_count']:
                    comparison['improvement_needed'].append('Virtual Tours')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'Room Types':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'room_type_count': amber_data.get('room_type_count', 0),
                'total_tenancies': amber_data.get('total_tenancies', 0),
                'total_available_tenancies': amber_data.get('total_available_tenancies', 0),  # NEW: Available tenancies
                'category_counts': amber_data.get('category_counts', {}),
                'category_tenancy_counts': amber_data.get('category_tenancy_counts', {}),
                'category_available_tenancy_counts': amber_data.get('category_available_tenancy_counts', {}),  # NEW: Available by category
                'total_room_images': amber_data.get('total_room_images', 0),
                'total_room_videos': amber_data.get('total_room_videos', 0)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'room_type_count': uhomes_data.get('room_type_count', 0),
                'total_tenancies': uhomes_data.get('total_tenancies', 0),
                'total_available_tenancies': uhomes_data.get('total_available_tenancies', 0),  # NEW: Available tenancies
                'category_counts': uhomes_data.get('category_counts', {}),
                'category_tenancy_counts': uhomes_data.get('category_tenancy_counts', {}),
                'category_available_tenancy_counts': uhomes_data.get('category_available_tenancy_counts', {}),  # NEW: Available by category
                'total_room_images': uhomes_data.get('total_room_images', 0),
                'total_room_videos': uhomes_data.get('total_room_videos', 0)
            }
            
            # Find differences and track improvement needed
            if comparison['amber']['room_type_count'] != comparison['uhomes']['room_type_count']:
                comparison['differences'].append(
                    f"Room Types: Amber has {comparison['amber']['room_type_count']}, "
                    f"UHomes has {comparison['uhomes']['room_type_count']}"
                )
                if comparison['uhomes']['room_type_count'] > comparison['amber']['room_type_count']:
                    comparison['improvement_needed'].append('Room Type Count')
                    comparison['uhomes_better_count'] += 1
            
            # Compare total tenancies (all including sold out)
            if comparison['amber']['total_tenancies'] != comparison['uhomes']['total_tenancies']:
                comparison['differences'].append(
                    f"Total Tenancies: Amber has {comparison['amber']['total_tenancies']}, "
                    f"UHomes has {comparison['uhomes']['total_tenancies']}"
                )
                if comparison['uhomes']['total_tenancies'] > comparison['amber']['total_tenancies']:
                    comparison['improvement_needed'].append('Total Tenancies')
                    comparison['uhomes_better_count'] += 1
            
            # Compare available tenancies (NEW: matches what website shows)
            amber_available = comparison['amber']['total_available_tenancies']
            uhomes_available = comparison['uhomes']['total_available_tenancies']
            if amber_available != uhomes_available:
                comparison['differences'].append(
                    f"Available Tenancies: Amber has {amber_available}, UHomes has {uhomes_available}"
                )
                if uhomes_available > amber_available:
                    comparison['improvement_needed'].append('Available Tenancies')
                    comparison['uhomes_better_count'] += 1
            
            # Compare categories (room type counts)
            amber_cats = comparison['amber']['category_counts']
            uhomes_cats = comparison['uhomes']['category_counts']
            for cat in ['Studio', 'Ensuite', 'Non Ensuite']:
                amber_count = amber_cats.get(cat, 0)
                uhomes_count = uhomes_cats.get(cat, 0)
                if amber_count != uhomes_count:
                    comparison['differences'].append(
                        f"{cat} Room Types: Amber has {amber_count}, UHomes has {uhomes_count}"
                    )
                    if uhomes_count > amber_count:
                        comparison['improvement_needed'].append(f'{cat} Room Type Count')
                        comparison['uhomes_better_count'] += 1
            
            # Compare total tenancy counts per category (all tenancies)
            amber_tenancy_cats = comparison['amber']['category_tenancy_counts']
            uhomes_tenancy_cats = comparison['uhomes']['category_tenancy_counts']
            for cat in ['Studio', 'Ensuite', 'Non Ensuite']:
                amber_tenancy = amber_tenancy_cats.get(cat, 0)
                uhomes_tenancy = uhomes_tenancy_cats.get(cat, 0)
                if amber_tenancy != uhomes_tenancy:
                    comparison['differences'].append(
                        f"{cat} Total Tenancies: Amber has {amber_tenancy}, UHomes has {uhomes_tenancy}"
                    )
                    if uhomes_tenancy > amber_tenancy:
                        comparison['improvement_needed'].append(f'{cat} Total Tenancy Count')
                        comparison['uhomes_better_count'] += 1
            
            # Compare available tenancy counts per category (NEW: matches what website shows)
            amber_available_cats = comparison['amber']['category_available_tenancy_counts']
            uhomes_available_cats = comparison['uhomes']['category_available_tenancy_counts']
            for cat in ['Studio', 'Ensuite', 'Non Ensuite']:
                amber_available = amber_available_cats.get(cat, 0)
                uhomes_available = uhomes_available_cats.get(cat, 0)
                if amber_available != uhomes_available:
                    comparison['differences'].append(
                        f"{cat} Available Tenancies: Amber has {amber_available}, UHomes has {uhomes_available}"
                    )
                    if uhomes_available > amber_available:
                        comparison['improvement_needed'].append(f'{cat} Available Tenancy Count')
                        comparison['uhomes_better_count'] += 1
        
        elif section_name == 'Amenities':
            # Only use property-level amenities (what's shown on website)
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'amenity_count': amber_data.get('amenity_count', 0),
                'amenities': amber_data.get('amenities', [])
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'amenity_count': uhomes_data.get('amenity_count', 0),
                'amenities': uhomes_data.get('amenities', [])
            }
            
            # Find differences using property-level amenities only
            if comparison['amber']['amenity_count'] != comparison['uhomes']['amenity_count']:
                comparison['differences'].append(
                    f"Amenities: Amber has {comparison['amber']['amenity_count']}, "
                    f"UHomes has {comparison['uhomes']['amenity_count']}"
                )
                if comparison['uhomes']['amenity_count'] > comparison['amber']['amenity_count']:
                    comparison['improvement_needed'].append('Amenity Count')
                    comparison['uhomes_better_count'] += 1
            
            # Find unique amenities using property-level amenities (normalized matching)
            def normalize_amenity(amenity):
                """Normalize amenity name for comparison"""
                import re
                if not amenity:
                    return ''
                normalized = re.sub(r'[^a-z0-9\s]', '', str(amenity).lower())
                return ' '.join(normalized.split())
            
            # Use property-level amenities for unique classification
            amber_amenities = comparison['amber']['amenities']
            uhomes_amenities = comparison['uhomes']['amenities']
            
            amber_norm = {normalize_amenity(a): a for a in amber_amenities if a and str(a).strip()}
            uhomes_norm = {normalize_amenity(u): u for u in uhomes_amenities if u and str(u).strip()}
            
            amber_keys = set(amber_norm.keys())
            uhomes_keys = set(uhomes_norm.keys())
            
            # Classify unique amenities (only what's in UHomes but not in Amber)
            only_uhomes_keys = uhomes_keys - amber_keys
            
            # Store list for sheet output (only unique to UHomes)
            comparison['uhomes']['only_uhomes_amenities'] = sorted([uhomes_norm[k] for k in only_uhomes_keys])
            comparison['only_uhomes_count'] = len(only_uhomes_keys)
            
            if only_uhomes_keys:
                comparison['differences'].append(
                    f"Only in UHomes: {', '.join(list(comparison['uhomes']['only_uhomes_amenities'])[:5])}"
                )
                if len(only_uhomes_keys) > 0:
                    comparison['improvement_needed'].append(f'Unique Amenities ({len(only_uhomes_keys)} more)')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'Payment':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'installment_options': amber_data.get('installment_options', []),
                'payment_methods': amber_data.get('payment_methods', []),
                'guarantor_required': amber_data.get('guarantor_required', False),
                'has_deposit_info': amber_data.get('has_deposit_info', False),
                'has_holding_fee': amber_data.get('has_holding_fee', False),
                'payment_policy_count': amber_data.get('payment_policy_count', 0)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'installment_options': uhomes_data.get('installment_options', []),
                'payment_methods': uhomes_data.get('payment_methods', []),
                'guarantor_required': uhomes_data.get('guarantor_required', False),
                'has_deposit_info': uhomes_data.get('has_deposit_info', False),
                'has_holding_fee': uhomes_data.get('has_holding_fee', False),
                'payment_policy_count': uhomes_data.get('payment_policy_count', 0)
            }
            
            # Find differences and track improvement needed
            amber_installments = len(comparison['amber']['installment_options']) if isinstance(comparison['amber']['installment_options'], list) else 0
            uhomes_installments = len(comparison['uhomes']['installment_options']) if isinstance(comparison['uhomes']['installment_options'], list) else 0
            
            if comparison['amber']['installment_options'] != comparison['uhomes']['installment_options']:
                comparison['differences'].append(
                    f"Installments: Amber {comparison['amber']['installment_options']}, "
                    f"UHomes {comparison['uhomes']['installment_options']}"
                )
                if uhomes_installments > amber_installments:
                    comparison['improvement_needed'].append('Installment Options')
                    comparison['uhomes_better_count'] += 1
            
            amber_methods = len(comparison['amber']['payment_methods']) if isinstance(comparison['amber']['payment_methods'], list) else 0
            uhomes_methods = len(comparison['uhomes']['payment_methods']) if isinstance(comparison['uhomes']['payment_methods'], list) else 0
            if uhomes_methods > amber_methods:
                comparison['improvement_needed'].append('Payment Methods')
                comparison['uhomes_better_count'] += 1
            
            if comparison['amber']['guarantor_required'] != comparison['uhomes']['guarantor_required']:
                comparison['differences'].append(
                    f"Guarantor: Amber {'required' if comparison['amber']['guarantor_required'] else 'not required'}, "
                    f"UHomes {'required' if comparison['uhomes']['guarantor_required'] else 'not required'}"
                )
                # If UHomes doesn't require guarantor but Amber does, that's better for UHomes
                if not comparison['uhomes']['guarantor_required'] and comparison['amber']['guarantor_required']:
                    comparison['improvement_needed'].append('Guarantor Not Required')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'Offers':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'offer_count': amber_data.get('offer_count', 0),
                'offers': amber_data.get('offers', [])
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'offer_count': uhomes_data.get('offer_count', 0),
                'offers': uhomes_data.get('offers', [])
            }
            
            if comparison['amber']['offer_count'] != comparison['uhomes']['offer_count']:
                comparison['differences'].append(
                    f"Offers: Amber has {comparison['amber']['offer_count']}, "
                    f"UHomes has {comparison['uhomes']['offer_count']}"
                )
                if comparison['uhomes']['offer_count'] > comparison['amber']['offer_count']:
                    comparison['improvement_needed'].append('Offer Count')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'About Property':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'word_count': amber_data.get('word_count', 0)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'word_count': uhomes_data.get('word_count', 0)
            }
            
            if comparison['amber']['word_count'] != comparison['uhomes']['word_count']:
                diff = abs(comparison['amber']['word_count'] - comparison['uhomes']['word_count'])
                comparison['differences'].append(
                    f"Word count: Amber has {comparison['amber']['word_count']}, "
                    f"UHomes has {comparison['uhomes']['word_count']} (difference: {diff})"
                )
                if comparison['uhomes']['word_count'] > comparison['amber']['word_count']:
                    comparison['improvement_needed'].append('Word Count')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'Cancellation':
            comparison['amber'] = {
                'has_content': amber_data.get('has_cancellation_policy', False),
                'policy_count': amber_data.get('detail_count', 0),
                'has_cooling_off': amber_data.get('has_cooling_off', False),
                'has_no_visa_no_pay': amber_data.get('has_no_visa_no_pay', False)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_cancellation_policy', False),
                'policy_count': uhomes_data.get('detail_count', 0),
                'has_cooling_off': uhomes_data.get('has_cooling_off', False),
                'has_no_visa_no_pay': uhomes_data.get('has_no_visa_no_pay', False)
            }
            
            if comparison['amber']['has_content'] != comparison['uhomes']['has_content']:
                comparison['differences'].append(
                    f"Cancellation Policy: Amber {'has' if comparison['amber']['has_content'] else 'does not have'}, "
                    f"UHomes {'has' if comparison['uhomes']['has_content'] else 'does not have'}"
                )
                if comparison['uhomes']['has_content'] and not comparison['amber']['has_content']:
                    comparison['improvement_needed'].append('Cancellation Policy')
                    comparison['uhomes_better_count'] += 1
            
            if comparison['amber']['policy_count'] != comparison['uhomes']['policy_count']:
                if comparison['uhomes']['policy_count'] > comparison['amber']['policy_count']:
                    comparison['improvement_needed'].append('Policy Count')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'FAQs':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'faq_count': amber_data.get('faq_count', 0)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'faq_count': uhomes_data.get('faq_count', 0)
            }
            
            if comparison['amber']['faq_count'] != comparison['uhomes']['faq_count']:
                comparison['differences'].append(
                    f"FAQs: Amber has {comparison['amber']['faq_count']}, "
                    f"UHomes has {comparison['uhomes']['faq_count']}"
                )
                if comparison['uhomes']['faq_count'] > comparison['amber']['faq_count']:
                    comparison['improvement_needed'].append('FAQ Count')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'Nearby Properties':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'property_count': amber_data.get('property_count', 0)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'property_count': uhomes_data.get('property_count', 0)
            }
            
            if comparison['amber']['property_count'] != comparison['uhomes']['property_count']:
                comparison['differences'].append(
                    f"Nearby Properties: Amber has {comparison['amber']['property_count']}, "
                    f"UHomes has {comparison['uhomes']['property_count']}"
                )
                if comparison['uhomes']['property_count'] > comparison['amber']['property_count']:
                    comparison['improvement_needed'].append('Nearby Properties')
                    comparison['uhomes_better_count'] += 1
        
        elif section_name == 'University Links':
            comparison['amber'] = {
                'has_content': amber_data.get('has_content', False),
                'university_count': amber_data.get('university_count', 0)
            }
            comparison['uhomes'] = {
                'has_content': uhomes_data.get('has_content', False),
                'university_count': uhomes_data.get('university_count', 0)
            }
            
            if comparison['amber']['university_count'] != comparison['uhomes']['university_count']:
                comparison['differences'].append(
                    f"University Links: Amber has {comparison['amber']['university_count']}, "
                    f"UHomes has {comparison['uhomes']['university_count']}"
                )
                if comparison['uhomes']['university_count'] > comparison['amber']['university_count']:
                    comparison['improvement_needed'].append('University Links')
                    comparison['uhomes_better_count'] += 1
        
        return comparison
    
    def _get_hierarchical_headers(self) -> tuple:
        """
        Get 3-row hierarchical headers for Sheets
        
        Returns:
            Tuple of (row1_sections, row2_subsections, row3_platforms, merge_ranges, row2_merge_ranges)
            merge_ranges: List of dicts with merge info for section headers (row 1)
            row2_merge_ranges: List of dicts with merge info for sub-section headers (row 2)
        """
        # Row 1: Section names (will be merged)
        row1 = ['Property_ID', 'Property_Name', 'Link']
        
        # Row 2: Sub-section names
        row2 = ['', '', '']  # First 3 columns empty (for Property_ID, Name, Link)
        
        # Row 3: Platform names (Amber | UHomes)
        row3 = ['', '', '']  # First 3 columns empty
        
        # Track merge ranges: {section_name: (start_col, end_col)}
        merge_ranges = []
        row2_merge_ranges = []  # Track merges for row 2 sub-sections
        current_col = 3  # Start after Property_ID, Property_Name, Link (0-indexed: 0,1,2)
        
        # Hero & Media section (SIMPLIFIED: 5 columns only)
        section_start = current_col
        subsections = ['Images', 'Videos', 'Virtual Tours', 'Lives', 'By Tenants']
        for sub in subsections:
            sub_start = current_col
            row2.extend([sub, ''])  # Sub-section name, empty (for UHomes)
            row3.extend(['Amber', 'UHomes'])
            # Track merge for this sub-section (spans 2 columns)
            row2_merge_ranges.append({
                'subsection': sub,
                'start_col': sub_start + 1,  # 1-indexed
                'end_col': sub_start + 2,
                'row': 2
            })
            current_col += 2
        merge_ranges.append({
            'section': 'Hero & Media',
            'start_col': section_start + 1,  # 1-indexed for Sheets API
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Hero & Media'] * (current_col - section_start))
        
        # Offers section
        section_start = current_col
        sub_start = current_col
        row2.extend(['Count', ''])
        row3.extend(['Amber', 'UHomes'])
        row2_merge_ranges.append({
            'subsection': 'Count',
            'start_col': sub_start + 1,
            'end_col': sub_start + 2,
            'row': 2
        })
        current_col += 2
        merge_ranges.append({
            'section': 'Offers',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Offers'] * (current_col - section_start))
        
        # About Property section
        section_start = current_col
        sub_start = current_col
        row2.extend(['Word Count', ''])
        row3.extend(['Amber', 'UHomes'])
        row2_merge_ranges.append({
            'subsection': 'Word Count',
            'start_col': sub_start + 1,
            'end_col': sub_start + 2,
            'row': 2
        })
        current_col += 2
        merge_ranges.append({
            'section': 'About Property',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['About Property'] * (current_col - section_start))
        
        # Room Types section
        section_start = current_col
        subsections = ['Room Type Count', 'Available Tenancies', 'Total Tenancies', 'Studio Available', 'Ensuite Available', 'Non Ensuite Available']
        for sub in subsections:
            sub_start = current_col
            row2.extend([sub, ''])
            row3.extend(['Amber', 'UHomes'])
            row2_merge_ranges.append({
                'subsection': sub,
                'start_col': sub_start + 1,
                'end_col': sub_start + 2,
                'row': 2
            })
            current_col += 2
        merge_ranges.append({
            'section': 'Room Types',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Room Types'] * (current_col - section_start))
        
        # Amenities section (property-level only)
        section_start = current_col
        # Count sub-section (spans 2 columns)
        sub_start = current_col
        row2.extend(['Count', ''])
        row3.extend(['Amber', 'UHomes'])
        row2_merge_ranges.append({
            'subsection': 'Count',
            'start_col': sub_start + 1,
            'end_col': sub_start + 2,
            'row': 2
        })
        current_col += 2
        # Unique to UHomes count (single column)
        row2.append('Unique to UHomes')
        row3.append('Count')
        current_col += 1
        # Only in UHomes (JSON List) - single column
        row2.append('Only in UHomes')
        row3.append('(JSON List)')
        current_col += 1
        merge_ranges.append({
            'section': 'Amenities',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Amenities'] * (current_col - section_start))
        
        # Payment section
        section_start = current_col
        subsections = ['Installment Options', 'Payment Methods', 'Guarantor Required']
        for sub in subsections:
            sub_start = current_col
            row2.extend([sub, ''])
            row3.extend(['Amber', 'UHomes'])
            row2_merge_ranges.append({
                'subsection': sub,
                'start_col': sub_start + 1,
                'end_col': sub_start + 2,
                'row': 2
            })
            current_col += 2
        merge_ranges.append({
            'section': 'Payment',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Payment'] * (current_col - section_start))
        
        # Cancellation section
        section_start = current_col
        subsections = ['Has Policy', 'Policy Count']
        for sub in subsections:
            sub_start = current_col
            row2.extend([sub, ''])
            row3.extend(['Amber', 'UHomes'])
            row2_merge_ranges.append({
                'subsection': sub,
                'start_col': sub_start + 1,
                'end_col': sub_start + 2,
                'row': 2
            })
            current_col += 2
        merge_ranges.append({
            'section': 'Cancellation',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Cancellation'] * (current_col - section_start))
        
        # FAQs section
        section_start = current_col
        sub_start = current_col
        row2.extend(['Count', ''])
        row3.extend(['Amber', 'UHomes'])
        row2_merge_ranges.append({
            'subsection': 'Count',
            'start_col': sub_start + 1,
            'end_col': sub_start + 2,
            'row': 2
        })
        current_col += 2
        merge_ranges.append({
            'section': 'FAQs',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['FAQs'] * (current_col - section_start))
        
        # Nearby Properties section
        section_start = current_col
        sub_start = current_col
        row2.extend(['Count', ''])
        row3.extend(['Amber', 'UHomes'])
        row2_merge_ranges.append({
            'subsection': 'Count',
            'start_col': sub_start + 1,
            'end_col': sub_start + 2,
            'row': 2
        })
        current_col += 2
        merge_ranges.append({
            'section': 'Nearby Properties',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['Nearby Properties'] * (current_col - section_start))
        
        # University Links section
        section_start = current_col
        sub_start = current_col
        row2.extend(['Count', ''])
        row3.extend(['Amber', 'UHomes'])
        row2_merge_ranges.append({
            'subsection': 'Count',
            'start_col': sub_start + 1,
            'end_col': sub_start + 2,
            'row': 2
        })
        current_col += 2
        merge_ranges.append({
            'section': 'University Links',
            'start_col': section_start + 1,
            'end_col': current_col,
            'row': 1
        })
        row1.extend(['University Links'] * (current_col - section_start))
        
        # Total Improvement Areas (single column, spans all 3 rows)
        row1.append('Total Improvement Areas')
        row2.append('')
        row3.append('')
        merge_ranges.append({
            'section': 'Total Improvement Areas',
            'start_col': current_col + 1,
            'end_col': current_col + 1,
            'row': 1,
            'span_rows': True  # Merge across 3 rows
        })
        
        return row1, row2, row3, merge_ranges, row2_merge_ranges
    
    def _get_sheets_headers(self) -> List[str]:
        """Get flat column headers (for backward compatibility)"""
        _, row2, row3, _, _ = self._get_hierarchical_headers()
        # Return row3 (platform names) as the actual column headers
        return row3
    
    def _generate_sheets_row(self, comparison: Dict[str, Any], property_link: str = '') -> List[Any]:
        """Generate a flat row for Sheets from comparison data"""
        sections = comparison.get('sections', {})
        
        # Helper to get values safely
        def get_section_value(section_name: str, key: str, platform: str, default=0):
            section = sections.get(section_name, {})
            platform_data = section.get(platform, {})
            return platform_data.get(key, default)
        
        def get_bool_value(value):
            return 'Yes' if value else 'No'
        
        # Helper to get list length
        def get_list_length(section_name: str, key: str, platform: str):
            value = get_section_value(section_name, key, platform, [])
            return len(value) if isinstance(value, list) else 0
        
        # Calculate total improvement areas
        total_improvement = sum(
            section.get('uhomes_better_count', 0) 
            for section in sections.values()
        )
        
        # Build row
        row = [
            comparison.get('property_id', ''),
            comparison.get('property_name', ''),
            property_link,
            # Hero & Media (SIMPLIFIED: 5 columns only)
            get_section_value('Hero & Media', 'image_count', 'amber', 0),
            get_section_value('Hero & Media', 'image_count', 'uhomes', 0),
            get_section_value('Hero & Media', 'video_count', 'amber', 0),  # Total videos (includes video tours)
            get_section_value('Hero & Media', 'video_count', 'uhomes', 0),
            get_section_value('Hero & Media', 'virtual_tour_count', 'amber', 0),  # Total virtual tours (includes 360° and 3D)
            get_section_value('Hero & Media', 'virtual_tour_count', 'uhomes', 0),
            get_section_value('Hero & Media', 'live_count', 'amber', 0),  # Lives (UHomes only)
            get_section_value('Hero & Media', 'live_count', 'uhomes', 0),
            get_section_value('Hero & Media', 'by_tenant_count', 'amber', 0),  # By Tenants (UHomes only)
            get_section_value('Hero & Media', 'by_tenant_count', 'uhomes', 0),
            # Offers
            get_section_value('Offers', 'offer_count', 'amber', 0),
            get_section_value('Offers', 'offer_count', 'uhomes', 0),
            # About Property
            get_section_value('About Property', 'word_count', 'amber', 0),
            get_section_value('About Property', 'word_count', 'uhomes', 0),
            # Room Types
            get_section_value('Room Types', 'room_type_count', 'amber', 0),
            get_section_value('Room Types', 'room_type_count', 'uhomes', 0),
            # Available tenancies (matches website display)
            get_section_value('Room Types', 'total_available_tenancies', 'amber', 0) if get_section_value('Room Types', 'total_available_tenancies', 'amber', None) is not None else get_section_value('Room Types', 'total_tenancies', 'amber', 0),
            get_section_value('Room Types', 'total_available_tenancies', 'uhomes', 0) if get_section_value('Room Types', 'total_available_tenancies', 'uhomes', None) is not None else get_section_value('Room Types', 'total_tenancies', 'uhomes', 0),
            # Total tenancies (all inventory including sold out)
            get_section_value('Room Types', 'total_tenancies', 'amber', 0),
            get_section_value('Room Types', 'total_tenancies', 'uhomes', 0),
            # Available tenancy counts per category (matches website)
            get_section_value('Room Types', 'category_available_tenancy_counts', 'amber', {}).get('Studio', 0) if isinstance(get_section_value('Room Types', 'category_available_tenancy_counts', 'amber', {}), dict) else (get_section_value('Room Types', 'category_tenancy_counts', 'amber', {}).get('Studio', 0) if isinstance(get_section_value('Room Types', 'category_tenancy_counts', 'amber', {}), dict) else 0),
            get_section_value('Room Types', 'category_available_tenancy_counts', 'uhomes', {}).get('Studio', 0) if isinstance(get_section_value('Room Types', 'category_available_tenancy_counts', 'uhomes', {}), dict) else (get_section_value('Room Types', 'category_tenancy_counts', 'uhomes', {}).get('Studio', 0) if isinstance(get_section_value('Room Types', 'category_tenancy_counts', 'uhomes', {}), dict) else 0),
            get_section_value('Room Types', 'category_available_tenancy_counts', 'amber', {}).get('Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_available_tenancy_counts', 'amber', {}), dict) else (get_section_value('Room Types', 'category_tenancy_counts', 'amber', {}).get('Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_tenancy_counts', 'amber', {}), dict) else 0),
            get_section_value('Room Types', 'category_available_tenancy_counts', 'uhomes', {}).get('Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_available_tenancy_counts', 'uhomes', {}), dict) else (get_section_value('Room Types', 'category_tenancy_counts', 'uhomes', {}).get('Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_tenancy_counts', 'uhomes', {}), dict) else 0),
            get_section_value('Room Types', 'category_available_tenancy_counts', 'amber', {}).get('Non Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_available_tenancy_counts', 'amber', {}), dict) else (get_section_value('Room Types', 'category_tenancy_counts', 'amber', {}).get('Non Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_tenancy_counts', 'amber', {}), dict) else 0),
            get_section_value('Room Types', 'category_available_tenancy_counts', 'uhomes', {}).get('Non Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_available_tenancy_counts', 'uhomes', {}), dict) else (get_section_value('Room Types', 'category_tenancy_counts', 'uhomes', {}).get('Non Ensuite', 0) if isinstance(get_section_value('Room Types', 'category_tenancy_counts', 'uhomes', {}), dict) else 0),
            # Amenities (property-level only)
            get_section_value('Amenities', 'amenity_count', 'amber', 0),
            get_section_value('Amenities', 'amenity_count', 'uhomes', 0),
            # Unique to UHomes count
            sections.get('Amenities', {}).get('only_uhomes_count', 0),
            # Only in UHomes (JSON list)
            json.dumps(sections.get('Amenities', {}).get('uhomes', {}).get('only_uhomes_amenities', [])),
            # Payment
            get_list_length('Payment', 'installment_options', 'amber'),
            get_list_length('Payment', 'installment_options', 'uhomes'),
            get_list_length('Payment', 'payment_methods', 'amber'),
            get_list_length('Payment', 'payment_methods', 'uhomes'),
            get_bool_value(get_section_value('Payment', 'guarantor_required', 'amber', False)),
            get_bool_value(get_section_value('Payment', 'guarantor_required', 'uhomes', False)),
            # Cancellation
            get_bool_value(get_section_value('Cancellation', 'has_content', 'amber', False)),
            get_bool_value(get_section_value('Cancellation', 'has_content', 'uhomes', False)),
            get_section_value('Cancellation', 'policy_count', 'amber', 0),
            get_section_value('Cancellation', 'policy_count', 'uhomes', 0),
            # FAQs
            get_section_value('FAQs', 'faq_count', 'amber', 0),
            get_section_value('FAQs', 'faq_count', 'uhomes', 0),
            # Nearby Properties
            get_section_value('Nearby Properties', 'property_count', 'amber', 0),
            get_section_value('Nearby Properties', 'property_count', 'uhomes', 0),
            # University Links
            get_section_value('University Links', 'university_count', 'amber', 0),
            get_section_value('University Links', 'university_count', 'uhomes', 0),
            # Total Improvement Areas
            total_improvement
        ]
        
        return row
    
    def _calculate_summary(self, sections: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate summary metrics"""
        summary = {
            'total_sections': len(sections),
            'sections_with_differences': 0,
            'sections_with_content_amber': 0,
            'sections_with_content_uhomes': 0,
            'key_differences': []
        }
        
        for section_name, section_data in sections.items():
            amber_has = section_data.get('amber', {}).get('has_content', False)
            uhomes_has = section_data.get('uhomes', {}).get('has_content', False)
            
            if amber_has:
                summary['sections_with_content_amber'] += 1
            if uhomes_has:
                summary['sections_with_content_uhomes'] += 1
            
            differences = section_data.get('differences', [])
            if differences:
                summary['sections_with_differences'] += 1
                summary['key_differences'].extend(differences[:2])  # Top 2 per section
        
        return summary
    
    def generate_report(self, property_id: str, output_format: str = 'text') -> str:
        """
        Generate a human-readable comparison report
        
        Args:
            property_id: Property ID
            output_format: 'text' or 'json'
            
        Returns:
            Report string
        """
        comparison = self.compare_property(property_id)
        
        if 'error' in comparison:
            return f"Error: {comparison['error']}"
        
        if output_format == 'json':
            return json.dumps(comparison, indent=2, ensure_ascii=False)
        
        # Text format
        report_lines = []
        report_lines.append("="*80)
        report_lines.append(f"PROPERTY COMPARISON REPORT")
        report_lines.append("="*80)
        report_lines.append(f"Property ID: {comparison['property_id']}")
        report_lines.append(f"Property Name: {comparison['property_name']}")
        report_lines.append(f"Compared At: {comparison['compared_at']}")
        report_lines.append("")
        
        # Summary
        summary = comparison['summary']
        report_lines.append("SUMMARY")
        report_lines.append("-"*80)
        report_lines.append(f"Total Sections: {summary['total_sections']}")
        report_lines.append(f"Sections with Content (Amber): {summary['sections_with_content_amber']}")
        report_lines.append(f"Sections with Content (UHomes): {summary['sections_with_content_uhomes']}")
        report_lines.append(f"Sections with Differences: {summary['sections_with_differences']}")
        report_lines.append("")
        
        if summary['key_differences']:
            report_lines.append("KEY DIFFERENCES")
            report_lines.append("-"*80)
            for diff in summary['key_differences'][:10]:  # Top 10
                report_lines.append(f"  • {diff}")
            report_lines.append("")
        
        # Section details
        report_lines.append("SECTION DETAILS")
        report_lines.append("-"*80)
        
        for section_name, section_data in comparison['sections'].items():
            report_lines.append(f"\n{section_name}")
            report_lines.append("-"*40)
            
            amber = section_data.get('amber', {})
            uhomes = section_data.get('uhomes', {})
            differences = section_data.get('differences', [])
            
            # Show key metrics (SIMPLIFIED)
            if section_name == 'Hero & Media':
                report_lines.append(f"  Amber: {amber.get('image_count', 0)} images, "
                                  f"{amber.get('video_count', 0)} videos, "
                                  f"{amber.get('virtual_tour_count', 0)} virtual tours")
                report_lines.append(f"  UHomes: {uhomes.get('image_count', 0)} images, "
                                  f"{uhomes.get('video_count', 0)} videos, "
                                  f"{uhomes.get('virtual_tour_count', 0)} virtual tours, "
                                  f"{uhomes.get('live_count', 0)} lives, "
                                  f"{uhomes.get('by_tenant_count', 0)} by tenants")
            
            elif section_name == 'Room Types':
                report_lines.append(f"  Amber: {amber.get('room_type_count', 0)} room types, "
                                  f"{amber.get('total_tenancies', 0)} tenancies")
                report_lines.append(f"  UHomes: {uhomes.get('room_type_count', 0)} room types, "
                                  f"{uhomes.get('total_tenancies', 0)} tenancies")
                
                # Show categories
                amber_cats = amber.get('category_counts', {})
                uhomes_cats = uhomes.get('category_counts', {})
                if amber_cats or uhomes_cats:
                    report_lines.append(f"  Categories - Amber: {amber_cats}, UHomes: {uhomes_cats}")
            
            elif section_name == 'Amenities':
                report_lines.append(f"  Amber: {amber.get('amenity_count', 0)} amenities")
                report_lines.append(f"  UHomes: {uhomes.get('amenity_count', 0)} amenities")
            
            elif section_name == 'Payment':
                report_lines.append(f"  Amber: {len(amber.get('installment_options', []))} installment options, "
                                  f"Guarantor: {'Yes' if amber.get('guarantor_required') else 'No'}")
                report_lines.append(f"  UHomes: {len(uhomes.get('installment_options', []))} installment options, "
                                  f"Guarantor: {'Yes' if uhomes.get('guarantor_required') else 'No'}")
            
            else:
                # Generic display
                amber_has = amber.get('has_content', False)
                uhomes_has = uhomes.get('has_content', False)
                report_lines.append(f"  Amber: {'Has content' if amber_has else 'No content'}")
                report_lines.append(f"  UHomes: {'Has content' if uhomes_has else 'No content'}")
            
            # Show differences
            if differences:
                report_lines.append(f"  Differences:")
                for diff in differences[:3]:  # Top 3 per section
                    report_lines.append(f"    • {diff}")
        
        report_lines.append("")
        report_lines.append("="*80)
        
        return "\n".join(report_lines)
    
    def compare_all_properties(self, write_to_sheets: bool = True) -> List[Dict[str, Any]]:
        """
        Compare all properties and optionally write to Sheets
        
        Args:
            write_to_sheets: If True, write results to V0_Comparison_Results sheet
            
        Returns:
            List of comparison dictionaries
        """
        logger.info("\n" + "="*80)
        logger.info("COMPARING ALL PROPERTIES")
        logger.info("="*80)
        
        try:
            # Get all properties
            input_df = self.sheets.read_sheet('Input_Properties')
            scraped_df = input_df[input_df['Status'] == 'scraped']
            
            if len(scraped_df) == 0:
                logger.info("No scraped properties found")
                return []
            
            logger.info(f"Found {len(scraped_df)} properties to compare")
            
            comparisons = []
            property_links = {}  # Store links for each property
            
            for idx, row in scraped_df.iterrows():
                property_id = row['Property_ID']
                property_links[property_id] = row.get('Amber_URL', '')  # Use Amber URL as link
                logger.info(f"\nComparing {property_id}...")
                
                comparison = self.compare_property(property_id)
                if 'error' not in comparison:
                    comparisons.append(comparison)
            
            logger.info(f"\n✅ Compared {len(comparisons)} properties")
            
            # Write to Sheets if requested
            if write_to_sheets and comparisons:
                self.write_comparison_to_sheets(comparisons, property_links)
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing all properties: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def write_comparison_to_sheets(self, comparisons: List[Dict[str, Any]], property_links: Dict[str, str]):
        """
        Write comparison results to Google Sheets
        
        Args:
            comparisons: List of comparison dictionaries
            property_links: Dictionary mapping property_id to link
        """
        logger.info("\n" + "="*80)
        logger.info("WRITING COMPARISON RESULTS TO SHEETS")
        logger.info("="*80)
        
        sheet_name = 'V0_Comparison_Results'
        
        try:
            # Get hierarchical headers
            row1_sections, row2_subsections, row3_platforms, merge_ranges, row2_merge_ranges = self._get_hierarchical_headers()
            
            # Check if sheet exists, create if not
            try:
                self.sheets.read_sheet(sheet_name)
                logger.info(f"Sheet '{sheet_name}' exists, will update")
            except:
                logger.info(f"Creating new sheet '{sheet_name}'")
                self.sheets.create_sheet(sheet_name, rows=1000, cols=len(row3_platforms))
                import time
                time.sleep(2)  # Wait for sheet creation
            
            # Ensure all rows have same length and are properly formatted
            max_len = max(len(row1_sections), len(row2_subsections), len(row3_platforms))
            
            # Pad rows to same length with empty strings
            row1_padded = list(row1_sections) + [''] * (max_len - len(row1_sections))
            row2_padded = list(row2_subsections) + [''] * (max_len - len(row2_subsections))
            row3_padded = list(row3_platforms) + [''] * (max_len - len(row3_platforms))
            
            # Ensure all values are strings (not None)
            row1_clean = [str(v) if v is not None else '' for v in row1_padded]
            row2_clean = [str(v) if v is not None else '' for v in row2_padded]
            row3_clean = [str(v) if v is not None else '' for v in row3_padded]
            
            # Write 3-row headers all at once for proper alignment
            worksheet = self.sheets.workbook.worksheet(sheet_name)
            
            # Unmerge all cells in first 3 rows to avoid conflicts
            try:
                from gspread import utils
                range_end = utils.rowcol_to_a1(3, max_len)
                # Unmerge cells in header range
                worksheet.unmerge_cells(f'A1:{range_end}')
                import time
                time.sleep(1)
            except Exception as e:
                logger.debug(f"Could not unmerge (may not be merged): {e}")
            
            # Write all 3 rows together
            from gspread import utils
            range_end = utils.rowcol_to_a1(3, max_len)
            headers = [row1_clean, row2_clean, row3_clean]
            worksheet.update(values=headers, range_name=f'A1:{range_end}')
            import time
            time.sleep(2)  # Wait for write to complete
            
            # Merge cells for section headers (row 1)
            try:
                from gspread import utils
                for merge_info in merge_ranges:
                    start_col = merge_info['start_col']
                    end_col = merge_info['end_col']
                    row = merge_info['row']
                    
                    if merge_info.get('span_rows'):
                        # Merge across 3 rows (for Total Improvement Areas)
                        start_cell = utils.rowcol_to_a1(row, start_col)
                        end_cell = utils.rowcol_to_a1(row + 2, end_col)
                        worksheet.merge_cells(f'{start_cell}:{end_cell}')
                    else:
                        # Merge across columns in row 1 only
                        start_cell = utils.rowcol_to_a1(row, start_col)
                        end_cell = utils.rowcol_to_a1(row, end_col)
                        worksheet.merge_cells(f'{start_cell}:{end_cell}')
                
                logger.info(f"   Merged {len(merge_ranges)} section headers (row 1)")
                
                # Merge cells for sub-section headers (row 2)
                for merge_info in row2_merge_ranges:
                    start_col = merge_info['start_col']
                    end_col = merge_info['end_col']
                    row = merge_info['row']
                    
                    # Merge across columns in row 2
                    start_cell = utils.rowcol_to_a1(row, start_col)
                    end_cell = utils.rowcol_to_a1(row, end_col)
                    worksheet.merge_cells(f'{start_cell}:{end_cell}')
                
                logger.info(f"   Merged {len(row2_merge_ranges)} sub-section headers (row 2)")
            except Exception as e:
                logger.warning(f"Could not merge cells (you can merge manually): {e}")
            
            logger.info(f"✅ Set up hierarchical headers (3 rows) in sheet '{sheet_name}'")
            logger.info(f"   Merged {len(merge_ranges)} section headers")
            import time
            time.sleep(1)
            
            # Generate rows
            rows = []
            for comparison in comparisons:
                property_id = comparison.get('property_id', '')
                link = property_links.get(property_id, '')
                row = self._generate_sheets_row(comparison, link)
                rows.append(row)
            
            # Clear existing data and write new data
            worksheet = self.sheets.workbook.worksheet(sheet_name)
            # Don't clear - we already wrote headers above
            # worksheet.clear()  # Commented out - headers already written
            
            # Write data rows starting from row 4 (after 3 header rows)
            if rows:
                worksheet.update(values=rows, range_name='A4')
            
            logger.info(f"✅ Written {len(rows)} properties to '{sheet_name}' sheet")
            logger.info(f"   Columns: {len(row3_platforms)}")
            logger.info(f"   Header rows: 3 (Sections → Sub-sections → Platforms)")
            logger.info(f"   Data rows: {len(rows)}")
            
            # Note: Conditional formatting should be set up manually in Google Sheets
            # Red: Where Amber < UHomes (improvement needed)
            # Green: Where Amber > UHomes (doing well)
            logger.info("\n📝 Note: Set up conditional formatting in Google Sheets:")
            logger.info("   - Red: Where UHomes value > Amber value (improvement needed)")
            logger.info("   - Green: Where Amber value > UHomes value (doing well)")
            logger.info("   - Freeze first 3 columns (Property_ID, Property_Name, Link)")
            
        except Exception as e:
            logger.error(f"Error writing to Sheets: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function for CLI usage"""
    import sys
    
    print("\n" + "="*80)
    print("V0 PROPERTY COMPARISON TOOL")
    print("="*80)
    print("\nSimple property-level comparison between Amber and UHomes")
    print("="*80 + "\n")
    
    comparator = V0PropertyComparison()
    
    if len(sys.argv) > 1:
        # Compare specific property
        property_id = sys.argv[1]
        report = comparator.generate_report(property_id)
        print(report)
    else:
        # Compare all properties and write to Sheets
        print("\nComparing all properties and writing to Sheets...")
        comparisons = comparator.compare_all_properties(write_to_sheets=True)
        
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        
        if comparisons:
            print(f"\n✅ Compared {len(comparisons)} properties")
            print(f"📊 Results written to 'V0_Comparison_Results' sheet")
            
            # Show summary
            total_improvement_areas = sum(
                sum(section.get('uhomes_better_count', 0) for section in comp.get('sections', {}).values())
                for comp in comparisons
            )
            properties_with_issues = sum(
                1 for comp in comparisons
                if sum(section.get('uhomes_better_count', 0) for section in comp.get('sections', {}).values()) > 0
            )
            
            print(f"\n📈 Summary:")
            print(f"   Properties with improvement areas: {properties_with_issues}/{len(comparisons)}")
            print(f"   Total improvement areas found: {total_improvement_areas}")
            
            # Show top 5 properties needing most improvement
            properties_with_counts = [
                (comp['property_id'], comp['property_name'], 
                 sum(section.get('uhomes_better_count', 0) for section in comp.get('sections', {}).values()))
                for comp in comparisons
            ]
            properties_with_counts.sort(key=lambda x: x[2], reverse=True)
            
            if properties_with_counts:
                print(f"\n🔴 Top 5 Properties Needing Most Improvement:")
                for prop_id, prop_name, count in properties_with_counts[:5]:
                    if count > 0:
                        print(f"   {prop_id}: {prop_name} - {count} improvement areas")
        else:
            print("\n⚠️ No properties compared")
        
        print("\n" + "="*80)
        print("✅ Comparison complete!")
        print("="*80 + "\n")


if __name__ == "__main__":
    main()

