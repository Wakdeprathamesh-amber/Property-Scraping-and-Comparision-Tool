"""
Amber API Scraper
Uses direct Amber API to fetch structured property data
More accurate and reliable than HTML scraping
"""

import re
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from html.parser import HTMLParser
import requests
from src.utils.logger import setup_logger


class LinkExtractor(HTMLParser):
    """Extract links from HTML content"""
    def __init__(self):
        super().__init__()
        self.links = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self.links.append(attr_value)


class AmberAPIScraper:
    """
    Scrapes Amber properties using their direct API
    
    API Endpoint: https://base.amberstudent.com/api/v0/inventories/{canonicalName}
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.api_base_url = "https://base.amberstudent.com/api/v0/inventories"
        self.logger.info("Amber API scraper initialized")
    
    def extract_canonical_name(self, url: str) -> str:
        """
        Extract canonical name from Amber URL
        
        Args:
            url: Amber property URL (e.g., https://amberstudent.com/places/ben-russell-court-leicester-1608300341147)
            
        Returns:
            Canonical name (e.g., 'ben-russell-court-leicester-1608300341147')
        """
        try:
            url_obj = urlparse(url)
            path_parts = url_obj.path.split('/')
            # Get the last part of the path which should be the canonical name
            canonical_name = path_parts[-1] if path_parts[-1] else path_parts[-2]
            return canonical_name
        except Exception as e:
            raise ValueError(f'Invalid Amber URL format: {e}')
    
    def fetch_property_data(self, canonical_name: str) -> Dict[str, Any]:
        """
        Fetch property data from Amber API
        
        Args:
            canonical_name: Property canonical name
            
        Returns:
            JSON response from API
        """
        api_url = f"{self.api_base_url}/{canonical_name}"
        
        self.logger.info(f"Fetching Amber property data: {canonical_name}")
        
        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"✅ Successfully fetched Amber property data")
            return data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API request failed: {e}")
            raise Exception(f"Failed to fetch Amber property: {e}")
    
    def fetch_room_types(self, canonical_name: str) -> List[Dict[str, Any]]:
        """
        Fetch individual room types from Amber API (includes tenancies in children)
        
        Args:
            canonical_name: Property canonical name
            
        Returns:
            List of room types with tenancy details in children field
        """
        api_url = f"{self.api_base_url}/{canonical_name}/room_types"
        
        self.logger.info(f"Fetching Amber room types: {canonical_name}")
        
        all_room_types = []
        page = 1
        total_count = None
        max_pages = 10  # Safety limit to prevent infinite loops
        
        try:
            while page <= max_pages:
                # Add pagination parameter (use 'p' not 'page')
                paginated_url = f"{api_url}?p={page}" if page > 1 else api_url
                response = requests.get(paginated_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    result_data = data.get('data', {})
                    room_types = result_data.get('result', [])
                    meta = result_data.get('meta', {})
                    
                    # Get total count from first page
                    if total_count is None:
                        total_count = meta.get('count', 0)
                    
                    if room_types:
                        all_room_types.extend(room_types)
                        self.logger.info(f"✅ Fetched page {page}: {len(room_types)} room types (total: {len(all_room_types)}/{total_count})")
                        
                        # Check if we've fetched all room types
                        if total_count > 0 and len(all_room_types) >= total_count:
                            break
                        
                        # Check if there are more pages - stop if next is None or if we got fewer items than limit
                        next_page = meta.get('next')
                        limit = meta.get('limit', 20)
                        
                        if next_page is None or len(room_types) < limit:
                            break
                        
                        page += 1
                    else:
                        # No more room types
                        break
                else:
                    if page == 1:
                        self.logger.warning(f"⚠️ Room types endpoint returned {response.status_code}, may not be available")
                    break
                    
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"⚠️ Could not fetch room types: {e}")
            return []
        
        self.logger.info(f"✅ Successfully fetched {len(all_room_types)} room types total")
        return all_room_types
    
    def fetch_pricing_units(self, canonical_name: str) -> List[Dict[str, Any]]:
        """
        Fetch pricing units/tenancies from Amber API (DEPRECATED - use fetch_room_types instead)
        
        Args:
            canonical_name: Property canonical name
            
        Returns:
            List of pricing units with tenancy details
        """
        # Try pricing-units endpoint
        api_url = f"{self.api_base_url}/{canonical_name}/pricing-units"
        
        self.logger.info(f"Fetching Amber pricing units: {canonical_name}")
        
        try:
            response = requests.get(api_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Successfully fetched pricing units")
                return data.get('data', []) if isinstance(data, dict) else data if isinstance(data, list) else []
            else:
                self.logger.warning(f"⚠️ Pricing units endpoint returned {response.status_code}, may not be available")
                return []
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"⚠️ Could not fetch pricing units: {e}")
            return []
    
    def extract_links_from_html(self, html_content: str) -> List[str]:
        """Extract all links from HTML content"""
        if not html_content:
            return []
        
        extractor = LinkExtractor()
        try:
            extractor.feed(html_content)
            return extractor.links
        except Exception as e:
            self.logger.warning(f"Error extracting links from HTML: {e}")
            return []
    
    def extract_hero_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hero section features from API data"""
        meta = data.get('data', {}).get('meta', {})
        videos = data.get('data', {}).get('videos', [])
        virtual_views = data.get('data', {}).get('virtual_views', [])
        
        features = {
            'has_360_tour': len(virtual_views) > 0,
            'has_3d_tour': any('3d' in v.get('type', '').lower() or '3-d' in v.get('type', '').lower() for v in virtual_views),
            'has_video_tour': len(videos) > 0,
            'has_map': meta.get('is_map_view_enabled', False),
            'has_map_toggle': meta.get('is_map_view_enabled', False),  # Assume toggle if map exists
            'has_street_view': False,  # Not directly available in API
            'has_price_display': bool(data.get('data', {}).get('pricing', {})),
            'video_count': len(videos),
            'virtual_tour_count': len(virtual_views),
            'total_videos_count': meta.get('total_videos_count', 0),
            'total_virtual_views_count': meta.get('total_virtual_views_count', 0)
        }
        
        return features
    
    def extract_property_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional property metadata from API"""
        api_data = data.get('data', {})
        meta = api_data.get('meta', {})
        
        metadata = {
            'property_id': api_data.get('id'),
            'inventory_no': api_data.get('inventory_no'),
            'canonical_name': api_data.get('canonical_name'),
            'status': api_data.get('status'),
            'available': api_data.get('available'),
            'source': api_data.get('source'),
            'source_link': api_data.get('source_link'),
            'provider_id': api_data.get('provider_id'),
            'region_id': api_data.get('region_id'),
            'created_at': api_data.get('created_at'),
            'updated_at': api_data.get('updated_at'),
            'weekly_price': api_data.get('weekly_price'),
            'inventory_visits': api_data.get('inventory_visits'),
            'revenue': api_data.get('revenue'),
            'payment_types': api_data.get('payment_types', []),
            'highlights': api_data.get('highlights', []),
            'tags': api_data.get('tags', []),
            'owner': api_data.get('owner', {}),
            'location': api_data.get('location', {}),
            'location_coordinates': api_data.get('location_coordinates'),
            'property_info': {
                'unit_count': meta.get('unit_count'),
                'max_area': meta.get('max_area'),
                'min_area': meta.get('min_area'),
                'area_unit': meta.get('area_unit'),
                'max_bedroom_count': meta.get('max_bedroom_count'),
                'min_bedroom_count': meta.get('min_bedroom_count'),
                'max_bathroom_count': meta.get('max_bathroom_count'),
                'min_bathroom_count': meta.get('min_bathroom_count'),
                'unit_types': meta.get('unit_types', []),
                'year_of_construction': meta.get('year_of_construction'),
                'highest_floor': None,  # Extract from property_info_tags
                'build_year': None  # Extract from property_info_tags
            },
            'amenity_prices': meta.get('amenity_prices', {}),
            'facts': meta.get('facts', []),
            'property_info_tags': meta.get('property_info_tags', []),
            'floor': meta.get('floor'),
            'facing': meta.get('facing'),
            'types': meta.get('types', []),
            'guarantor_required': meta.get('guarantor_required'),
            'lease_duration_unit': meta.get('lease_duration_unit'),
            'max_available_from': meta.get('max_available_from'),
            'min_available_from': meta.get('min_available_from'),
            'max_available_lease_duration': meta.get('max_available_lease_duration'),
            'min_available_lease_duration': meta.get('min_available_lease_duration')
        }
        
        # Extract from property_info_tags
        property_info_tags = meta.get('property_info_tags', [])
        for tag in property_info_tags:
            tag_type = tag.get('type', '')
            tag_value = tag.get('value', '')
            if tag_type == 'highest_floor':
                metadata['property_info']['highest_floor'] = tag_value
            elif tag_type == 'build_in_year':
                metadata['property_info']['build_year'] = tag_value
        
        return metadata
    
    def extract_payment_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed payment information from description array"""
        descriptions = data.get('data', {}).get('description', [])
        payment_details = {
            'installment_options': [],
            'payment_methods': [],
            'guarantor_required': False,
            'holding_fee': None,
            'deposit': None,
            'booking_deposit': None
        }
        
        for desc in descriptions:
            tag = desc.get('tag', '')
            name = desc.get('name', '')
            value = desc.get('value', '')
            short_text = desc.get('short_text', '')
            
            # Extract installment options with full details
            if tag == 'payment_instalment_plan':
                installment_option = desc.get('payment_installment_option', [])
                if installment_option:
                    payment_details['installment_options'] = installment_option
                # Also extract from short_text
                if '1, 2, 4' in short_text or '1, 2, 4' in value:
                    payment_details['installment_options'] = [1, 2, 4]
                # Store full installment details
                payment_details['installment_details'] = {
                    'value': value,
                    'short_text': short_text,
                    'display_name': desc.get('display_name', '')
                }
            
            # Extract payment methods with full details
            if tag == 'mode_of_payment':
                # Extract payment methods from value
                if 'credit' in value.lower() or 'debit' in value.lower():
                    payment_details['payment_methods'].append('Credit/Debit Card')
                if 'bank transfer' in value.lower():
                    payment_details['payment_methods'].append('Bank Transfer')
                if 'phone' in value.lower():
                    payment_details['payment_methods'].append('Phone Payment')
                # Store full payment method details (includes exclusions like "no American Express")
                payment_details['payment_method_details'] = {
                    'value': value,
                    'short_text': short_text,
                    'display_name': desc.get('display_name', '')
                }
            
            # Extract guarantor requirement with full details
            if tag == 'guarantor_requirement':
                payment_details['guarantor_required'] = True
                payment_details['guarantor_details'] = {
                    'value': value,
                    'short_text': short_text,
                    'display_name': desc.get('display_name', '')
                }
            
            # Extract holding fee
            if tag == 'fully_refundable_holding_fee':
                # Extract amount from value (e.g., "£25")
                fee_match = re.search(r'£(\d+)', value)
                if fee_match:
                    payment_details['holding_fee'] = {
                        'amount': int(fee_match.group(1)),
                        'currency': 'GBP',
                        'refundable': 'refundable' in value.lower()
                    }
            
            # Extract booking deposit
            if tag == 'booking_deposit':
                payment_details['booking_deposit'] = {
                    'required': 'not accepting' not in value.lower(),
                    'details': value
                }
        
        # Extract deposit from pricing
        pricing = data.get('data', {}).get('pricing', {})
        if pricing.get('deposit'):
            payment_details['deposit'] = {
                'amount': pricing.get('deposit'),
                'currency': '£' if pricing.get('currency') == 'pound' else '$'
            }
        
        return payment_details
    
    def extract_offers_details(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed offers information"""
        offers = []
        
        # Extract from offers array
        offers_array = data.get('data', {}).get('offers', [])
        for offer in offers_array:
            offers.append({
                'name': offer.get('name', ''),
                'description': offer.get('description', ''),
                'type': offer.get('type', 'general'),
                'valid_from': offer.get('valid_from'),
                'valid_to': offer.get('valid_to')
            })
        
        # Extract from cro_tags (cashback, amber_sale)
        meta = data.get('data', {}).get('meta', {})
        cro_tags = meta.get('cro_tags', {})
        
        # Cashback offer
        if cro_tags.get('cashback'):
            offers.append({
                'name': 'Cashback',
                'description': f"£{cro_tags.get('cashback')} cashback",
                'amount': cro_tags.get('cashback'),
                'type': 'cashback'
            })
        
        # Amber sale offer
        amber_sale = cro_tags.get('amber_sale', {})
        if amber_sale.get('status') == 'true' and amber_sale.get('offer'):
            offers.append({
                'name': 'Amber Sale',
                'description': amber_sale.get('offer'),
                'type': 'amber_sale',
                'status': amber_sale.get('status')
            })
        
        return offers
    
    def extract_videos(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract video information"""
        videos = data.get('data', {}).get('videos', [])
        video_list = []
        
        for video in videos:
            video_list.append({
                'url': video.get('path', ''),
                'type': video.get('type', ''),
                'caption': video.get('caption', ''),
                'thumbnail_url': video.get('thumbnail_url', ''),
                'duration': video.get('duration', ''),
                'platform': video.get('platform', '')
            })
        
        return video_list
    
    def extract_virtual_tours(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract 360° virtual tour information"""
        virtual_views = data.get('data', {}).get('virtual_views', [])
        tours = []
        
        for view in virtual_views:
            tour_type = view.get('type', '').lower()
            is_360 = 'virtual' in tour_type or '360' in tour_type or 'vr' in tour_type
            is_3d = '3d' in tour_type or '3-d' in tour_type
            
            tours.append({
                'url': view.get('id', ''),
                'type': view.get('type', ''),
                'is_360_tour': is_360,
                'is_3d_tour': is_3d
            })
        
        return tours
    
    def extract_nearby_properties(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract nearby/similar properties if available"""
        # Check if API has nearby properties endpoint or field
        # Currently not available in main API response, but structure ready for future
        nearby = data.get('data', {}).get('nearby_properties', [])
        if not nearby:
            # Check meta for similar properties
            meta = data.get('data', {}).get('meta', {})
            nearby = meta.get('similar_properties', [])
        
        properties = []
        for prop in nearby:
            properties.append({
                'name': prop.get('name', ''),
                'url': prop.get('url', ''),
                'distance': prop.get('distance', ''),
                'price': prop.get('price', '')
            })
        
        return properties
    
    def json_to_markdown(self, data: Dict[str, Any]) -> str:
        """
        Convert Amber API JSON response to markdown format
        Compatible with existing analysis pipeline
        
        Args:
            data: JSON data from Amber API
            
        Returns:
            Markdown string
        """
        markdown_parts = []
        
        # Property Name
        property_name = data.get('data', {}).get('name', 'Unknown Property')
        markdown_parts.append(f"# {property_name}\n")
        
        # Hero & Media Section
        hero_features = self.extract_hero_features(data)
        markdown_parts.append(f"\n## Hero & Media\n\n")
        markdown_parts.append(f"**Media Features:**\n")
        if hero_features['has_360_tour']:
            markdown_parts.append(f"- ✅ 360° Virtual Tour Available ({hero_features['virtual_tour_count']} tours)\n")
        if hero_features['has_3d_tour']:
            markdown_parts.append(f"- ✅ 3D Tour Available\n")
        if hero_features['has_video_tour']:
            markdown_parts.append(f"- ✅ Video Tours Available ({hero_features['video_count']} videos)\n")
        if hero_features['has_map']:
            markdown_parts.append(f"- ✅ Map View Available\n")
        if hero_features['has_price_display']:
            markdown_parts.append(f"- ✅ Price Display in Hero\n")
        markdown_parts.append(f"\n**Media Counts:**\n")
        markdown_parts.append(f"- Total Videos: {hero_features['total_videos_count']}\n")
        markdown_parts.append(f"- Total Virtual Views: {hero_features['total_virtual_views_count']}\n")
        
        # Videos
        videos = self.extract_videos(data)
        if videos:
            markdown_parts.append(f"\n**Videos:**\n")
            for video in videos:
                video_type = video.get('type', 'video').replace('_', ' ').title()
                markdown_parts.append(f"- **{video_type}**: {video.get('caption', 'Property Tour')} - {video.get('url', '')}\n")
        
        # Virtual Tours (360°/3D)
        virtual_tours = self.extract_virtual_tours(data)
        if virtual_tours:
            markdown_parts.append(f"\n**Virtual Tours:**\n")
            for tour in virtual_tours:
                tour_type = tour.get('type', 'Virtual Tour')
                markdown_parts.append(f"- **{tour_type}**: {tour.get('url', '')}\n")
        
        # Description
        descriptions = data.get('data', {}).get('description', [])
        all_links = []
        for desc in descriptions:
            desc_name = desc.get('name', '')
            desc_value = desc.get('value', '')
            
            # Extract links from HTML
            links = self.extract_links_from_html(desc_value)
            all_links.extend(links)
            
            if desc_name == 'about':
                markdown_parts.append(f"\n## About Property\n\n{desc_value}\n")
            elif 'cancellation' in desc_name.lower():
                markdown_parts.append(f"\n## Cancellation Policy\n\n{desc_value}\n")
            elif desc_name == 'payment':
                # Payment details will be handled separately
                pass
            else:
                markdown_parts.append(f"\n## {desc_name.title()}\n\n{desc_value}\n")
        
        # Pricing
        pricing = data.get('data', {}).get('pricing', {})
        if pricing:
            currency = '£' if pricing.get('currency') == 'pound' else '$'
            min_price = pricing.get('min_price', 'N/A')
            max_price = pricing.get('max_price', 'N/A')
            duration = pricing.get('duration', 'week')
            deposit = pricing.get('deposit', 0)
            
            markdown_parts.append(f"\n## Pricing\n\n")
            markdown_parts.append(f"Price Range: {currency}{min_price} - {currency}{max_price} / {duration}\n")
            markdown_parts.append(f"Deposit: {currency}{deposit}\n")
        
        # Payment Details (Enhanced)
        payment_details = self.extract_payment_details(data)
        if payment_details['installment_options'] or payment_details['payment_methods']:
            markdown_parts.append(f"\n## Payment Details\n\n")
            if payment_details['installment_options']:
                options = ', '.join(map(str, payment_details['installment_options']))
                markdown_parts.append(f"**Installment Options:** {options} instalments available\n")
            if payment_details['payment_methods']:
                methods = ', '.join(payment_details['payment_methods'])
                markdown_parts.append(f"**Payment Methods:** {methods}\n")
            if payment_details['guarantor_required']:
                markdown_parts.append(f"**Guarantor:** Required\n")
            if payment_details['holding_fee']:
                fee = payment_details['holding_fee']
                refundable = "Refundable" if fee.get('refundable') else "Non-refundable"
                markdown_parts.append(f"**Holding Fee:** {fee.get('currency', '£')}{fee.get('amount', '')} ({refundable})\n")
            if payment_details['deposit']:
                dep = payment_details['deposit']
                markdown_parts.append(f"**Deposit:** {dep.get('currency', '£')}{dep.get('amount', '')}\n")
        
        # Room Types (from meta.unit_types if room_types not available)
        room_types = data.get('data', {}).get('room_types', [])
        meta = data.get('data', {}).get('meta', {})
        
        if room_types:
            markdown_parts.append(f"\n## Room Types\n\n")
            currency = '£' if pricing.get('currency') == 'pound' else '$' if pricing else '£'
            for room in room_types:
                room_name = room.get('name', 'Unknown')
                room_price = room.get('price', 'N/A')
                room_size = room.get('size') or room.get('dimensions', '')
                markdown_parts.append(f"- **{room_name}**: {currency}{room_price}")
                if room_size:
                    markdown_parts[-1] += f" ({room_size})"
                markdown_parts[-1] += "\n"
        elif meta.get('unit_types'):
            # Extract room types from meta.unit_types
            markdown_parts.append(f"\n## Room Types\n\n")
            unit_types = meta.get('unit_types', [])
            max_area = meta.get('max_area')
            min_area = meta.get('min_area')
            area_unit = meta.get('area_unit', 'sqm')
            currency = '£' if pricing.get('currency') == 'pound' else '$' if pricing else '£'
            min_price = pricing.get('min_price', '') if pricing else ''
            max_price = pricing.get('max_price', '') if pricing else ''
            
            for unit_type in unit_types:
                unit_name = unit_type.replace('_', ' ').title()
                markdown_parts.append(f"- **{unit_name}**")
                if min_price and max_price:
                    markdown_parts[-1] += f": {currency}{min_price} - {currency}{max_price}"
                elif min_price:
                    markdown_parts[-1] += f": From {currency}{min_price}"
                if min_area and max_area:
                    markdown_parts[-1] += f" ({min_area}-{max_area} {area_unit})"
                elif max_area:
                    markdown_parts[-1] += f" (Up to {max_area} {area_unit})"
                markdown_parts[-1] += "\n"
        
        # Property Highlights
        highlights = data.get('data', {}).get('highlights', [])
        if highlights:
            markdown_parts.append(f"\n## Property Highlights\n\n")
            for highlight in highlights:
                markdown_parts.append(f"- {highlight}\n")
        
        # Property Information (from meta)
        property_info_tags = meta.get('property_info_tags', [])
        if property_info_tags:
            markdown_parts.append(f"\n## Property Information\n\n")
            for tag in property_info_tags:
                tag_type = tag.get('type', '').replace('_', ' ').title()
                tag_value = tag.get('value', '')
                markdown_parts.append(f"- **{tag_type}**: {tag_value}\n")
        
        # Utility Pricing (from meta.amenity_prices)
        amenity_prices = meta.get('amenity_prices', {})
        if amenity_prices:
            markdown_parts.append(f"\n## Utility Pricing\n\n")
            for utility_name, utility_data in amenity_prices.items():
                if isinstance(utility_data, dict):
                    utility_price = utility_data.get('price', '')
                    utility_currency = utility_data.get('currency', 'GBP')
                    utility_duration = utility_data.get('duration', 'weekly')
                    display_name = utility_data.get('display_name', utility_name.replace('_', ' ').title())
                    if utility_price:
                        currency_symbol = '£' if utility_currency == 'GBP' else '$'
                        markdown_parts.append(f"- **{display_name}**: {currency_symbol}{utility_price} / {utility_duration}\n")
        
        # Features/Amenities
        features = data.get('data', {}).get('features', [])
        if features:
            markdown_parts.append(f"\n## Amenities\n\n")
            for feature_group in features:
                group_name = feature_group.get('name', '')
                group_values = feature_group.get('values', [])
                
                if group_name:
                    markdown_parts.append(f"### {group_name}\n\n")
                
                for value in group_values:
                    value_name = value.get('name', '')
                    if value_name:
                        markdown_parts.append(f"- {value_name}\n")
        
        # Offers (Enhanced)
        offers = self.extract_offers_details(data)
        if offers:
            markdown_parts.append(f"\n## Offers\n\n")
            for offer in offers:
                offer_name = offer.get('name', 'Offer')
                offer_desc = offer.get('description', '')
                offer_type = offer.get('type', '')
                if offer.get('amount'):
                    markdown_parts.append(f"- **{offer_name}** ({offer_type}): {offer_desc}\n")
                else:
                    markdown_parts.append(f"- **{offer_name}** ({offer_type}): {offer_desc}\n")
        
        # FAQs
        faqs = data.get('data', {}).get('faqs', [])
        if faqs:
            markdown_parts.append(f"\n## FAQs\n\n")
            for faq in faqs:
                question = faq.get('question', '')
                answer = faq.get('answer', '')
                markdown_parts.append(f"### Q: {question}\n\nA: {answer}\n\n")
        
        # Nearby Locations
        distances = data.get('data', {}).get('meta', {}).get('distances', [])
        if distances:
            markdown_parts.append(f"\n## Nearby Locations\n\n")
            for dist in distances:
                place = dist.get('place', '')
                distance = dist.get('distance', '')
                markdown_parts.append(f"- **{place}**: {distance}\n")
        
        # Nearby Properties
        nearby_properties = self.extract_nearby_properties(data)
        if nearby_properties:
            markdown_parts.append(f"\n## Nearby Properties\n\n")
            for prop in nearby_properties:
                markdown_parts.append(f"- **{prop.get('name', '')}**: {prop.get('distance', '')} - {prop.get('url', '')}\n")
        
        # Images (Enhanced)
        images = data.get('data', {}).get('images', [])
        if images:
            markdown_parts.append(f"\n## Images\n\n")
            markdown_parts.append(f"Total Images: {len(images)}\n")
            for img in images[:10]:  # First 10 images
                img_url = img.get('url', '') or img.get('path', '') or img.get('base_path', '')
                img_type = img.get('type', '')
                img_caption = img.get('caption', '')
                if img_url:
                    if img_caption:
                        markdown_parts.append(f"- ![{img_caption}]({img_url}) - {img_type}\n")
                    else:
                        markdown_parts.append(f"- ![]({img_url}) - {img_type}\n")
        
        # Links
        if all_links:
            markdown_parts.append(f"\n## Links\n\n")
            unique_links = list(set(all_links))
            for link in unique_links[:20]:  # First 20 unique links
                markdown_parts.append(f"- {link}\n")
        
        return '\n'.join(markdown_parts)
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape Amber property using API
        
        Args:
            url: Amber property URL
            
        Returns:
            Dict with scraped data (compatible with Firecrawl format)
        """
        try:
            # Extract canonical name
            canonical_name = self.extract_canonical_name(url)
            
            # Fetch data from API
            api_data = self.fetch_property_data(canonical_name)
            
            # Convert to markdown
            markdown = self.json_to_markdown(api_data)
            
            # Extract metadata
            property_name = api_data.get('data', {}).get('name', 'Unknown Property')
            images = api_data.get('data', {}).get('images', [])
            # Extract all possible image URL fields
            image_urls = []
            for img in images:
                url = img.get('url') or img.get('path') or img.get('base_path', '')
                if url:
                    image_urls.append(url)
            
            # Extract links from all description HTML content
            links = []
            descriptions = api_data.get('data', {}).get('description', [])
            for desc in descriptions:
                desc_value = desc.get('value', '')
                if desc_value:
                    extracted_links = self.extract_links_from_html(desc_value)
                    links.extend(extracted_links)
            
            # Extract videos
            videos = self.extract_videos(api_data)
            video_urls = [v.get('url', '') for v in videos if v.get('url')]
            
            # Extract virtual tours
            virtual_tours = self.extract_virtual_tours(api_data)
            virtual_tour_urls = [vt.get('url', '') for vt in virtual_tours if vt.get('url')]
            
            # Extract hero features
            hero_features = self.extract_hero_features(api_data)
            
            # Extract payment details
            payment_details = self.extract_payment_details(api_data)
            
            # Extract offers
            offers = self.extract_offers_details(api_data)
            
            # Extract nearby properties
            nearby_properties = self.extract_nearby_properties(api_data)
            
            # Extract property metadata
            property_metadata = self.extract_property_metadata(api_data)
            
            # Remove duplicate links
            unique_links = list(set(links))
            
            self.logger.info(
                f"✅ Scraped successfully: {len(markdown)} chars markdown, "
                f"{len(image_urls)} images, {len(video_urls)} videos, "
                f"{len(virtual_tour_urls)} virtual tours, {len(unique_links)} links"
            )
            
            return {
                'success': True,
                'url': url,
                'markdown': markdown,
                'html': '',  # Not available from API
                'metadata': {
                    'title': property_name,
                    'description': api_data.get('data', {}).get('description', [{}])[0].get('value', '') if api_data.get('data', {}).get('description') else '',
                    'images': image_urls,
                    'links': unique_links,
                    'videos': video_urls,
                    'virtual_tours': virtual_tour_urls,
                    'hero_features': hero_features,
                    'payment_details': payment_details,
                    'offers': offers,
                    'nearby_properties': nearby_properties,
                    'property_metadata': property_metadata,
                    'highlights': property_metadata.get('highlights', []),
                    'tags': property_metadata.get('tags', []),
                    'location_details': property_metadata.get('location', {}),
                    'source_url': url
                },
                'scraper': 'amber_api',
                'raw_json': api_data  # Store raw JSON for detailed comparison
            }
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__,
                'scraper': 'amber_api'
            }


if __name__ == "__main__":
    # Test scraper
    scraper = AmberAPIScraper()
    
    test_url = "https://amberstudent.com/places/ben-russell-court-leicester-1608300341147"
    result = scraper.scrape_url(test_url)
    
    if result['success']:
        print(f"✅ Success! Property: {result['metadata']['title']}")
        print(f"Markdown length: {len(result['markdown'])} chars")
        print(f"Images: {len(result['metadata']['images'])}")
    else:
        print(f"❌ Failed: {result.get('error')}")


