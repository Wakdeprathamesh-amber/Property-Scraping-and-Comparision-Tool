"""
Simple LLM-based Comparator

Takes extracted data from both properties and generates comparison
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.utils.logger import setup_logger


class SimpleLLMComparator:
    """
    Compares two extracted property datasets using LLM
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    
    def compare(self, amber_data: Dict[str, Any], competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two properties and generate structured comparison
        
        Returns:
            Dict with section-by-section comparison, gaps, advantages
        """
        self.logger.info(
            f"Comparing {amber_data.get('property_name')} vs {competitor_data.get('property_name')}"
        )
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(amber_data, competitor_data)
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            result = json.loads(response.content)
            self.logger.info("Comparison complete")
            return result
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            return self._empty_comparison()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for comparison"""
        return """You are a property comparison specialist.

Compare two properties (Amber vs Competitor) section by section.

OUTPUT STRUCTURE:
{
  "section_comparisons": {
    "amenities": {
      "amber_present": true,
      "competitor_present": false,
      "amber_items": ["Gym", "Study Room"],
      "competitor_items": [],
      "amber_count": 6,
      "competitor_count": 0,
      "status": "amber_advantage",
      "gap_items": []
    }
  },
  "missing_in_amber": ["reviews_ratings", "offers_deals"],
  "missing_in_competitor": ["payment_options"],
  "unique_to_amber": ["cancellation_policies"],
  "unique_to_competitor": ["trust_badges"],
  "overall_similarity": 0.45,
  "amber_advantages": [
    "More comprehensive amenities section",
    "Detailed payment options"
  ],
  "competitor_advantages": [
    "Has reviews and ratings",
    "More detailed location info"
  ]
}

Be thorough and accurate."""
    
    def _build_user_prompt(self, amber: Dict, competitor: Dict) -> str:
        """Build user prompt with data"""
        return f"""Compare these two properties:

AMBER DATA:
{json.dumps(amber, indent=2)}

COMPETITOR DATA:
{json.dumps(competitor, indent=2)}

COMPARISON TASKS:
1. Compare each of 21 standard sections
2. Identify which sections are present in each
3. Count items in each section
4. List missing sections in each
5. Identify unique sections
6. List specific gaps (items in one but not other)
7. Calculate overall similarity (0-1)
8. List competitive advantages for each

Return complete JSON following the format in system prompt."""
    
    def _empty_comparison(self) -> Dict[str, Any]:
        """Empty comparison result"""
        return {
            "section_comparisons": {},
            "missing_in_amber": [],
            "missing_in_competitor": [],
            "unique_to_amber": [],
            "unique_to_competitor": [],
            "overall_similarity": 0.0,
            "amber_advantages": [],
            "competitor_advantages": []
        }

