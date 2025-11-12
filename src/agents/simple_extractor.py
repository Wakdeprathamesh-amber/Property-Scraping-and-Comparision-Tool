"""
Simple LLM-based Extractor - Replaces all complex parsers

Sends raw text directly to LLM with comprehensive prompt.
No parsing, no data loss, no complexity.
"""

from typing import Dict, Any, List
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.utils.logger import setup_logger


class SimpleLLMExtractor:
    """
    Single-purpose extractor that sends raw text to LLM
    and gets structured output following 21-section taxonomy
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Fast and cheap
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    
    def extract(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from raw input
        
        Args:
            raw_data: Dict with 'extracted_content' containing raw text
            
        Returns:
            Structured dict with all sections, items, counts
        """
        # Get raw text
        text = raw_data.get('extracted_content', {}).get('text', '')
        property_name = raw_data.get('property_name', 'Unknown')
        url = raw_data.get('url', '')
        
        if not text or len(text) < 50:
            self.logger.warning(f"Text too short: {len(text)} chars")
            return self._empty_result(property_name, url)
        
        self.logger.info(f"Extracting from {len(text)} chars of text for {property_name}")
        
        # Build comprehensive prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(text, property_name, url)
        
        # Call LLM
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            # Parse JSON response
            result = json.loads(response.content)
            
            self.logger.info(
                f"Extracted: {result.get('sections_count', 0)} sections, "
                f"{result.get('total_items', 0)} total items"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return self._empty_result(property_name, url)
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt"""
        return """You are a property data extraction specialist.

Your job: Extract ALL information from property listing text into structured JSON.

CRITICAL RULES:
1. Extract EVERYTHING - don't summarize or skip
2. Count ALL items accurately (amenities, room types, FAQs, etc.)
3. Use ONLY the 21 standard section names (listed below)
4. Preserve exact wording for items
5. Return valid JSON only

21 STANDARD SECTIONS (use these names exactly):
- hero_media
- property_overview
- address_core_details
- room_types
- pricing
- offers_deals
- amenities
- bills_included
- location_transport
- nearby_places
- payment_options
- booking_process
- cancellation_policies
- trust_badges
- faqs
- reviews_ratings
- contact_support
- similar_properties
- highlights
- safety_security
- company_info

OUTPUT FORMAT:
{
  "property_name": "Clean property name (not image alt text)",
  "url": "Property URL",
  "sections_count": 10,
  "total_items": 45,
  "total_word_count": 5000,
  "sections": [
    {
      "name": "amenities",
      "display_name": "Amenities",
      "content": "Full section text...",
      "items": ["Gym", "Study Room", "Courtyard"],
      "word_count": 150
    }
  ],
  "metrics": {
    "amenities_count": 6,
    "room_types_count": 4,
    "faqs_count": 5,
    "bills_included_count": 5,
    "payment_options_count": 3,
    "universities_mentioned": 3,
    "pois_count": 5,
    "reviews_count": 0,
    "trust_badges_count": 0,
    "safety_features_count": 0
  },
  "images_count": 20,
  "videos_count": 0
}

Be thorough. Extract everything."""
    
    def _build_user_prompt(self, text: str, property_name: str, url: str) -> str:
        """Build user prompt with actual data"""
        return f"""Extract ALL data from this property listing.

PROPERTY METADATA:
Property Name: {property_name}
URL: {url}

RAW TEXT (extract everything from this):
{text}

INSTRUCTIONS:
1. Find the REAL property name (skip image alt text like "...Bedroom" or "...Kitchen")
2. Count ALL amenities (Gym, Study Room, etc.)
3. Count ALL room types (1 Bed 1 Bath, etc.)
4. Count ALL FAQs (questions ending with ?)
5. Count ALL bills included (Heat, Hydro, Gas, etc.)
6. Count ALL universities mentioned
7. Count ALL nearby POIs (stations, parks, etc.)
8. Extract ALL sections you can identify
9. Map each section to one of the 21 standard names

Return complete JSON following the format specified in system prompt.
Be accurate with counts - they are critical!"""
    
    def _empty_result(self, property_name: str, url: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "property_name": property_name,
            "url": url,
            "sections_count": 0,
            "total_items": 0,
            "total_word_count": 0,
            "sections": [],
            "metrics": {
                "amenities_count": 0,
                "room_types_count": 0,
                "faqs_count": 0,
                "bills_included_count": 0,
                "payment_options_count": 0,
                "universities_mentioned": 0,
                "pois_count": 0,
                "reviews_count": 0,
                "trust_badges_count": 0,
                "safety_features_count": 0
            },
            "images_count": 0,
            "videos_count": 0
        }

