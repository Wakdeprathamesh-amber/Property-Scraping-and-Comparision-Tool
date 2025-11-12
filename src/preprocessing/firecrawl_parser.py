"""
Firecrawl Parser - Handles Firecrawl scraped content

Firecrawl outputs a specific markdown-like format that needs special handling
"""

from typing import Dict, Any, List
import re

from .base_parser import BaseParser
from src.models.canonical_format import (
    CanonicalFormat, PreSection, PricingInfo,
    ContactInfo, LocationInfo, ImageInfo, VideoInfo
)


class FirecrawlParser(BaseParser):
    """
    Parser optimized for Firecrawl scraped content
    Handles markdown headings, space-separated lists, nested sections
    """
    
    def parse(self, data: Dict[str, Any]) -> CanonicalFormat:
        """Parse Firecrawl format to CanonicalFormat"""
        
        self.logger.info(f"Parsing Firecrawl data for: {data.get('property_name', 'Unknown')}")
        
        extracted = data.get('extracted_content', {})
        text = extracted.get('text', '')
        
        # Fix property name (remove image alt text patterns)
        property_name = self._extract_real_property_name(text, data.get('property_name'))
        
        # Extract URL from user-provided data (more reliable than scraping)
        url = data.get('url', 'https://example.com')
        provider = data.get('provider')
        
        # Extract sections using Firecrawl-specific patterns
        sections = self._extract_firecrawl_sections(text)
        
        # Extract structured data
        pricing = self._extract_pricing_from_firecrawl(text)
        contact = self._extract_contact_from_firecrawl(text)
        location = self._extract_location_from_firecrawl(text, data)
        
        # Extract media
        images = self._extract_images_from_data(data)
        videos = self._extract_videos_from_data(data)
        
        # Create canonical format
        canonical = CanonicalFormat(
            source="firecrawl_scrape",
            property_name=property_name,
            url=url,
            provider=provider,
            sections=sections,
            pricing=pricing,
            contact=contact,
            location=location,
            images=images,
            videos=videos,
            raw_data=data
        )
        
        canonical.confidence_score = self._calculate_confidence_score(canonical)
        self._add_quality_flags(canonical)
        
        self.logger.info(
            f"Parsed Firecrawl data: {len(sections)} sections, "
            f"{canonical.get_total_word_count()} words"
        )
        
        return canonical
    
    def _extract_real_property_name(self, text: str, fallback: str) -> str:
        """
        Extract real property name, avoiding image alt text
        
        Firecrawl often puts image alt text as property_name
        Example bad: "1Ten on Whyte, Edmonton - Edmonton, Canada - 1 Bed 1 Bath - Bedroom"
        Example good: "1Ten On Whyte - Student Living"
        """
        # If fallback looks like image alt text, find real name
        if fallback and (' - Bedroom' in fallback or ' - Amenities' in fallback or ' - Kitchen' in fallback):
            # This is image alt text, find real name from headings
            lines = text.split('\n')
            for line in lines[:20]:
                # Look for markdown headings
                heading_match = re.match(r'^#+\s*(.+)$', line.strip())
                if heading_match:
                    candidate = heading_match.group(1).strip()
                    # Must be short enough and not generic
                    if (3 < len(candidate) < 80 and 
                        'Overview' not in candidate and
                        'Bedroom' not in candidate and
                        'Amenities' not in candidate):
                        return candidate
            
            # Extract from the alt text itself (first part before dashes)
            parts = fallback.split(' - ')
            if parts:
                return parts[0].strip()
        
        return fallback or "Unknown Property"
    
    def _extract_firecrawl_sections(self, text: str) -> List[PreSection]:
        """
        Extract sections from Firecrawl markdown format
        
        Firecrawl mixes:
        - ## Section Name
        - Navigation menus (to filter out)
        - Space-separated lists
        - Content blocks
        """
        sections = []
        
        # First, clean navigation noise
        text_cleaned = self._remove_navigation_noise(text)
        
        # Strategy 1: Extract by markdown headings (## and ###)
        heading_pattern = r'^##\s+(.+?)$\n(.*?)(?=\n##|\Z)'
        matches = re.finditer(heading_pattern, text_cleaned, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            heading = match.group(1).strip()
            content = match.group(2).strip()
            
            # Skip navigation sections
            if self._is_navigation_section(heading):
                continue
            
            if len(content) > 15:  # Has content
                section_name = self._infer_section_name(heading)
                
                # Extract items from content
                items = self._extract_items_from_firecrawl_content(content, section_name)
                
                sections.append(PreSection(
                    original_name=section_name,
                    display_name=heading,
                    content=content,
                    items=items
                ))
        
        # Strategy 2: Extract specific known sections (amenities, bills, FAQs, etc.)
        sections.extend(self._extract_special_sections(text_cleaned))
        
        # Deduplicate sections by name
        seen = set()
        unique_sections = []
        for section in sections:
            if section.original_name not in seen:
                seen.add(section.original_name)
                unique_sections.append(section)
            elif len(section.items) > len([s for s in unique_sections if s.original_name == section.original_name][0].items):
                # Replace with version that has more items
                unique_sections = [s for s in unique_sections if s.original_name != section.original_name]
                unique_sections.append(section)
                seen.add(section.original_name)
        
        return unique_sections
    
    def _remove_navigation_noise(self, text: str) -> str:
        """Remove navigation menus and repetitive elements"""
        # Remove lines that are clearly navigation
        lines = text.split('\n')
        clean_lines = []
        
        skip_keywords = ['Menu', 'Login', 'Sign Up', 'Shortlist', 'Support', 'Download App', 
                        'Play Store', 'App Store', 'Follow us', 'amber ©', 'Company', 'Discover',
                        'Share Listing', 'Favorites', 'Add a Property']
        
        for line in lines:
            # Skip if line is just navigation
            if any(kw in line for kw in skip_keywords) and len(line) < 100:
                continue
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _is_navigation_section(self, heading: str) -> bool:
        """Check if heading is navigation/menu"""
        nav_keywords = ['Nearby Locations', 'Similar Properties', 'Student Accommodations',
                       'Tourist Attractions', 'Universities in', 'Nearby Places', 
                       'Cities', 'Localities']
        return any(kw in heading for kw in nav_keywords)
    
    def _extract_items_from_firecrawl_content(self, content: str, section_name: str) -> List[str]:
        """
        Extract items from Firecrawl content
        
        Handles multiple formats:
        - Space-separated: "Gym  Study Room  Courtyard"
        - Newline separated: "Gym\nStudy Room\nCourtyard"
        - Bullet points: "- Gym\n- Study Room"
        - Mixed
        """
        items = []
        
        # Pattern 1: Bullet points (standard)
        items.extend(self._extract_items_from_text(content))
        
        # Pattern 2: Space-separated lists (Firecrawl specific!)
        # "Gym  Study Room  Courtyard Boardroom  On-Site Laundry"
        if not items or len(items) < 3:
            # Look for lines with multiple spaces between words
            for line in content.split('\n'):
                if '  ' in line:  # Multiple spaces indicate list
                    # Split by 2+ spaces
                    line_items = re.split(r'\s{2,}', line.strip())
                    for item in line_items:
                        item = item.strip()
                        if item and len(item) > 1 and len(item) < 100:
                            items.append(item)
        
        # Pattern 3: Newline-separated short lines (like amenities lists)
        if not items or len(items) < 3:
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            # If we have many short lines, they're probably list items
            short_lines = [l for l in lines if len(l) < 50 and len(l) > 2]
            if len(short_lines) >= 3:
                items.extend(short_lines[:20])
        
        # Pattern 4: FAQ questions (###)
        if 'faq' in section_name.lower() or 'question' in section_name.lower():
            questions = re.findall(r'###\s*(.+\?)', content)
            items.extend(questions)
        
        # Pattern 5: Room types ("4 Bed 2 Bath")
        if 'room' in section_name.lower():
            room_patterns = re.findall(r'(\d+\s*Bed\s*\d*\s*Bath)', content)
            items.extend(list(set(room_patterns)))
        
        # Deduplicate
        seen = set()
        unique_items = []
        for item in items:
            item_clean = item.strip()
            if item_clean and item_clean not in seen and len(item_clean) > 1:
                seen.add(item_clean)
                unique_items.append(item_clean)
        
        return unique_items[:50]
    
    def _extract_special_sections(self, text: str) -> List[PreSection]:
        """Extract sections that might not have clear ## headings"""
        sections = []
        
        # Amenities - look for the specific line with space-separated items
        # Example: "Gym  Study Room Courtyard Boardroom  On-Site Laundry  Study Lounge"
        amenities_keywords = ['Gym', 'Study Room', 'Courtyard', 'Boardroom', 'Laundry', 'Study Lounge']
        for line in text.split('\n'):
            if sum(1 for kw in amenities_keywords if kw in line) >= 3:
                # Use known amenity patterns to intelligently split
                items = []
                line_copy = line
                
                # Extract known multi-word amenities first
                known_patterns = [
                    'Study Room', 'Study Lounge', 'On-Site Laundry', 'In-Suite Laundry',
                    'Laundry Room', 'Fitness Center', 'Game Room', 'Common Room',
                    'Meeting Room', 'Board Room', 'Boardroom'
                ]
                
                for pattern in known_patterns:
                    if pattern in line_copy:
                        items.append(pattern)
                        line_copy = line_copy.replace(pattern, ' ', 1)  # Remove so we don't double-count
                
                # Now split remaining by spaces and extract single-word amenities
                remaining_words = line_copy.split()
                known_single = ['Gym', 'Courtyard', 'Pool', 'Cinema', 'Theater', 'Lounge', 
                               'Kitchen', 'Parking', 'Storage', 'Elevator', 'WiFi']
                
                for word in remaining_words:
                    word = word.strip()
                    if word in known_single and word not in ' '.join(items):
                        items.append(word)
                
                # Deduplicate and sort
                items = list(dict.fromkeys(items))  # Preserve order
                items = [i for i in items if len(i) > 2]
                
                if len(items) >= 3:
                    sections.append(PreSection(
                        original_name='amenities',
                        display_name='Amenities',
                        content=line,
                        items=items
                    ))
                    break
        
        # Bills Included - specific extraction
        # Example: "Heat  Hydro Gas Internet In-Suite Laundry"
        bills_patterns = ['Heat', 'Hydro', 'Gas', 'Internet']
        for line in text.split('\n'):
            if sum(1 for kw in bills_patterns if kw in line) >= 3:
                # Extract known bill patterns
                items = []
                line_copy = line
                
                known_bills = ['Heat', 'Hydro', 'Gas', 'Internet', 'In-Suite Laundry', 
                              'Electricity', 'Water', 'WiFi', 'Wi-Fi']
                
                for pattern in known_bills:
                    if pattern in line_copy:
                        items.append(pattern)
                
                # Deduplicate
                items = list(dict.fromkeys(items))
                
                if len(items) >= 3:
                    sections.append(PreSection(
                        original_name='bills_included',
                        display_name='Bills Included',
                        content=line,
                        items=items
                    ))
                    break
        
        # FAQs - extract questions (multiple patterns)
        faq_match = re.search(
            r'Frequently Asked Questions(.*?)(?=\n##[^#]|Show more|View less|Nearby Places|Student Accommodations|Universities in|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if faq_match:
            content = faq_match.group(1).strip()
            # Extract questions - try multiple patterns
            questions = []
            
            # Pattern 1: ### Question?
            questions.extend(re.findall(r'###\s*(.+\?)', content))
            
            # Pattern 2: Question without ###
            questions.extend(re.findall(r'^(.+\?)$', content, re.MULTILINE))
            
            # Deduplicate
            questions = list(dict.fromkeys(questions))
            
            if questions:
                sections.append(PreSection(
                    original_name='faqs',
                    display_name='FAQs',
                    content=content,
                    items=questions
                ))
        
        # Room Types - extract "X Bed Y Bath" patterns
        room_types = re.findall(r'(\d+\s*Bed\s*\d*\s*Bath)', text)
        if room_types:
            unique_rooms = list(set(room_types))
            # Find content around room types
            room_content = []
            for room in unique_rooms[:5]:
                # Get context around this room type
                pattern = re.escape(room) + r'.*?(?:\n\n|\n[A-Z]|$)'
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    room_content.append(match.group(0))
            
            if unique_rooms:
                sections.append(PreSection(
                    original_name='room_types',
                    display_name='Room Types',
                    content='\n\n'.join(room_content),
                    items=unique_rooms
                ))
        
        # Payment Policies
        payment_match = re.search(
            r'Payment Policies\s*\((\d+)\)(.*?)(?=\n##[^#]|Cancellation|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if payment_match:
            content = payment_match.group(2).strip()
            # Extract policy names
            policies = re.findall(r'^-\s*(.+?)$', content, re.MULTILINE)
            if policies:
                sections.append(PreSection(
                    original_name='payment',
                    display_name='Payment Policies',
                    content=content,
                    items=policies
                ))
        
        # Cancellation Policies
        cancel_match = re.search(
            r'Cancellation Policies\s*\((\d+)\)(.*?)(?=\n##[^#]|Frequently|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if cancel_match:
            content = cancel_match.group(2).strip()
            policies = re.findall(r'^-\s*(.+?)$', content, re.MULTILINE)
            if policies:
                sections.append(PreSection(
                    original_name='cancellation',
                    display_name='Cancellation Policies',
                    content=content,
                    items=policies
                ))
        
        # Offers
        offers_match = re.search(
            r'##\s*Offers\s*\((\d+)\)(.*?)(?=\n##[^#]|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if offers_match:
            content = offers_match.group(2).strip()
            offers = re.findall(r'^-\s*(.+?)$', content, re.MULTILINE)
            if offers:
                sections.append(PreSection(
                    original_name='offers',
                    display_name='Offers',
                    content=content,
                    items=offers
                ))
        
        return sections
    
    def _infer_section_name(self, heading: str) -> str:
        """Infer section name from Firecrawl heading"""
        heading_lower = heading.lower()
        
        # Direct mappings
        if 'amenities' in heading_lower or 'amenity' in heading_lower:
            return 'amenities'
        elif 'room types' in heading_lower or 'room type' in heading_lower:
            return 'room_types'
        elif 'pricing' in heading_lower or 'price' in heading_lower or 'fees' in heading_lower:
            return 'pricing'
        elif 'faq' in heading_lower or 'question' in heading_lower:
            return 'faqs'
        elif 'about' in heading_lower or 'overview' in heading_lower:
            return 'about'
        elif 'location' in heading_lower or 'commute' in heading_lower:
            return 'location'
        elif 'nearby' in heading_lower or 'surrounding' in heading_lower:
            return 'nearby_places'
        elif 'features' in heading_lower:
            return 'features'
        elif 'bills' in heading_lower and 'payment' in heading_lower:
            return 'bills_and_payments'
        elif 'bills' in heading_lower:
            return 'bills_included'
        elif 'payment' in heading_lower or 'policies' in heading_lower:
            return 'payment'
        elif 'cancellation' in heading_lower:
            return 'cancellation'
        elif 'offer' in heading_lower or 'deal' in heading_lower or 'promotion' in heading_lower:
            return 'offers'
        elif 'review' in heading_lower or 'rating' in heading_lower:
            return 'reviews'
        elif 'contact' in heading_lower or 'support' in heading_lower:
            return 'contact'
        else:
            # Clean heading to make a name
            return re.sub(r'[^\w\s]', '', heading_lower).replace(' ', '_')
    
    def _extract_pricing_from_firecrawl(self, text: str) -> PricingInfo:
        """Extract pricing from Firecrawl format"""
        pricing_data = self._extract_pricing(text)
        
        if pricing_data['min_price'] or pricing_data['max_price']:
            return PricingInfo(
                currency=pricing_data.get('currency', 'CAD'),  # Canadian property
                min_price=pricing_data['min_price'],
                max_price=pricing_data['max_price'],
                price_unit='monthly',
                raw_text=pricing_data.get('raw_text')
            )
        
        return None
    
    def _extract_contact_from_firecrawl(self, text: str) -> ContactInfo:
        """Extract contact info"""
        contact_data = self._extract_contact_info(text)
        
        if contact_data.get('email') or contact_data.get('phone'):
            return ContactInfo(
                email=contact_data.get('email'),
                phone=contact_data.get('phone')
            )
        
        return None
    
    def _extract_location_from_firecrawl(self, text: str, data: Dict) -> LocationInfo:
        """Extract location"""
        location_str = data.get('location')
        
        if location_str:
            return LocationInfo(
                address=location_str,
                city=self._extract_city_from_address(location_str),
                postcode=None
            )
        
        return None
    
    def _extract_images_from_data(self, data: Dict) -> List[ImageInfo]:
        """Extract images"""
        images = []
        extracted = data.get('extracted_content', {})
        images_data = extracted.get('images', [])
        
        for img in images_data:
            if isinstance(img, dict):
                url = img.get('url', '')
                if url and url.strip():
                    images.append(ImageInfo(
                        url=url,
                        alt=img.get('alt'),
                        title=img.get('title')
                    ))
        
        return images
    
    def _extract_videos_from_data(self, data: Dict) -> List[VideoInfo]:
        """Extract videos"""
        videos = []
        extracted = data.get('extracted_content', {})
        videos_data = extracted.get('videos')
        
        if videos_data and isinstance(videos_data, list):
            for vid in videos_data:
                if isinstance(vid, dict):
                    url = vid.get('url', '')
                    if url:
                        videos.append(VideoInfo(
                            url=url,
                            title=vid.get('title'),
                            thumbnail=vid.get('thumbnail')
                        ))
        
        return videos

