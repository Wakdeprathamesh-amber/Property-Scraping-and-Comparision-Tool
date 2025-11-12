"""
Detailed Section-Specific Analyzer

Performs in-depth quantitative analysis for each section.
This is called AFTER basic comparison to add detailed insights.
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.utils.logger import setup_logger


class DetailedSectionAnalyzer:
    """
    Performs deep section-by-section quantitative analysis
    """
    
    # All 21 standard sections
    STANDARD_SECTIONS = [
        "hero_media",
        "property_overview",
        "address_core_details",
        "room_types",
        "pricing",
        "offers_deals",
        "amenities",
        "bills_included",
        "location_transport",
        "nearby_places",
        "payment_options",
        "booking_process",
        "cancellation_policies",
        "trust_badges",
        "faqs",
        "reviews_ratings",
        "contact_support",
        "similar_properties",
        "highlights",
        "safety_security",
        "company_info"
    ]
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Use full model for detailed analysis
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    
    def analyze(
        self,
        amber_data: Dict[str, Any],
        competitor_data: Dict[str, Any],
        basic_comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform detailed section-specific analysis
        
        Returns:
            Dict with detailed metrics for all 21 sections
        """
        self.logger.info("Starting detailed section analysis...")
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(amber_data, competitor_data, basic_comparison)
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            result = json.loads(response.content)
            self.logger.info(f"Detailed analysis complete: {len(result.get('sections', {}))} sections analyzed")
            return result
            
        except Exception as e:
            self.logger.error(f"Detailed analysis failed: {e}")
            return self._empty_analysis()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for detailed analysis"""
        return f"""You are an expert property data analyst specializing in quantitative analysis.

Your task: Perform DEEP section-by-section analysis for ALL 21 standard sections.

21 STANDARD SECTIONS (analyze ALL of these):
{chr(10).join(f"- {s}" for s in self.STANDARD_SECTIONS)}

For EACH section, provide:
1. Presence status (✓ Present, ✗ Missing, ⚠ Partial)
2. Amber metrics (word count, item count, richness score 0-100)
3. Competitor metrics (word count, item count, richness score 0-100)
4. Specific items in each (list all)
5. Gap items (present in one but not other)
6. Quantitative comparison (which is better and by how much)
7. Strategic recommendations
8. Department-specific actions (Content, UX, SEO, Marketing, Product)

OUTPUT FORMAT:
{{
  "all_21_sections": {{
    "hero_media": {{
      "amber_present": true/false,
      "competitor_present": true/false,
      "status": "both_have" | "amber_only" | "competitor_only" | "neither",
      "status_icon": "⚖️" | "🏆" | "🚨" | "❌",
      "amber_metrics": {{
        "word_count": 150,
        "item_count": 5,
        "richness_score": 75,
        "specific_items": ["Item 1", "Item 2"]
      }},
      "competitor_metrics": {{
        "word_count": 200,
        "item_count": 7,
        "richness_score": 85,
        "specific_items": ["Item A", "Item B"]
      }},
      "gap_analysis": {{
        "missing_in_amber": ["Item A"],
        "missing_in_competitor": ["Item 1"]
      }},
      "quantitative_verdict": "Competitor has 33% more items and 40% more content",
      "recommendations": [
        "Add Item A to match competitor",
        "Enhance word count by 50 words"
      ],
      "department_actions": {{
        "content": "Add X, Y, Z",
        "ux": "Improve layout",
        "seo": "Add keywords",
        "marketing": "Highlight feature",
        "product": "Build feature"
      }}
    }}
  }},
  "quantitative_summary": {{
    "total_sections_amber": 15,
    "total_sections_competitor": 12,
    "sections_in_both": 10,
    "amber_only": 5,
    "competitor_only": 2,
    "neither": 4,
    "amber_total_content": 5000,
    "competitor_total_content": 4500,
    "amber_avg_richness": 72.5,
    "competitor_avg_richness": 68.3
  }}
}}

CRITICAL: Analyze ALL 21 sections. Don't skip any."""
    
    def _build_user_prompt(
        self,
        amber: Dict,
        competitor: Dict,
        basic_comparison: Dict
    ) -> str:
        """Build user prompt"""
        return f"""Perform detailed quantitative analysis on these properties:

AMBER DATA:
{json.dumps(amber, indent=2)}

COMPETITOR DATA:
{json.dumps(competitor, indent=2)}

BASIC COMPARISON (for context):
{json.dumps(basic_comparison, indent=2)}

ANALYSIS REQUIREMENTS:
1. Analyze ALL 21 standard sections
2. For sections not present, mark as "neither" and explain impact
3. Provide specific item-by-item comparison
4. Calculate precise metrics (word counts, item counts, scores)
5. Identify exact gaps (what's missing where)
6. Give actionable department-specific recommendations
7. Ensure richness scores are accurate (0-100 scale based on completeness and detail)

Return complete JSON with ALL 21 sections analyzed."""
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        empty_sections = {}
        for section in self.STANDARD_SECTIONS:
            empty_sections[section] = {
                "amber_present": False,
                "competitor_present": False,
                "status": "neither",
                "status_icon": "❌",
                "amber_metrics": {
                    "word_count": 0,
                    "item_count": 0,
                    "richness_score": 0,
                    "specific_items": []
                },
                "competitor_metrics": {
                    "word_count": 0,
                    "item_count": 0,
                    "richness_score": 0,
                    "specific_items": []
                },
                "gap_analysis": {
                    "missing_in_amber": [],
                    "missing_in_competitor": []
                },
                "quantitative_verdict": "No data available",
                "recommendations": [],
                "department_actions": {}
            }
        
        return {
            "all_21_sections": empty_sections,
            "quantitative_summary": {
                "total_sections_amber": 0,
                "total_sections_competitor": 0,
                "sections_in_both": 0,
                "amber_only": 0,
                "competitor_only": 0,
                "neither": 21,
                "amber_total_content": 0,
                "competitor_total_content": 0,
                "amber_avg_richness": 0,
                "competitor_avg_richness": 0
            }
        }

