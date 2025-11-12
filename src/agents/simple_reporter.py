"""
Simple LLM-based Report Generator

Takes comparison data and generates final markdown/HTML report
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.utils.logger import setup_logger
from src.agents.visual_reporter import VisualReportGenerator


class SimpleLLMReporter:
    """
    Generates comprehensive report from comparison data
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Use stronger model for report generation
            temperature=0.3
        )
        self.visual_generator = VisualReportGenerator()
    
    def generate_report(
        self,
        amber_data: Dict[str, Any],
        competitor_data: Dict[str, Any],
        comparison: Dict[str, Any],
        detailed_analysis: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Generate markdown and HTML reports
        
        Args:
            detailed_analysis: Optional detailed analysis with all 21 sections
        
        Returns:
            Dict with 'markdown' and 'html' keys
        """
        self.logger.info("Generating comprehensive report")
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(amber_data, competitor_data, comparison, detailed_analysis)
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            markdown = response.content
            
            # Generate beautiful visual HTML report
            html = self.visual_generator.generate_html_report(
                amber_data,
                competitor_data,
                comparison,
                markdown,
                detailed_analysis  # Pass detailed analysis for UI
            )
            
            self.logger.info(f"Report generated: {len(markdown)} chars markdown, {len(html)} chars HTML")
            
            return {
                "markdown": markdown,
                "html": html
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {
                "markdown": f"# Error\n\nReport generation failed: {e}",
                "html": f"<h1>Error</h1><p>Report generation failed: {e}</p>"
            }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for report generation"""
        return """You are a property comparison report writer.

Generate a COMPREHENSIVE markdown report comparing Amber vs Competitor.

REQUIRED SECTIONS:
1. Overview
2. Section Presence Matrix (21-section taxonomy table)
3. Quantitative Metrics Summary
4. Section-by-Section Comparison
5. Strategic Insights & Competitive Analysis
6. Actionable Recommendations by Department
7. Competitor Content Advantage Score
8. Overall Verdict

CRITICAL REQUIREMENTS:
- Use ACTUAL numbers from the data (no zeros if data exists!)
- Mark sections as ✅ Present or ❌ Not Present based on actual data
- Show ALL items from each section
- Give specific, actionable recommendations
- Calculate scores accurately
- Use tables for metrics
- Use emojis for visual clarity (✅ ❌ 🚨 🏆 etc.)

FORMAT:
- Markdown with proper headers (#, ##, ###)
- Tables for structured data
- Bullet lists for items
- Clear section breaks

Be thorough, accurate, and actionable."""
    
    def _build_user_prompt(
        self, 
        amber: Dict, 
        competitor: Dict, 
        comparison: Dict,
        detailed_analysis: Dict = None
    ) -> str:
        """Build user prompt with all data"""
        detailed_section = ""
        if detailed_analysis:
            detailed_section = f"""

DETAILED SECTION ANALYSIS (ALL 21 SECTIONS):
{json.dumps(detailed_analysis, indent=2)}

Use this detailed analysis to populate the Section Presence Matrix with ALL 21 sections."""
        
        return f"""Generate comprehensive property comparison report.

AMBER DATA:
Property: {amber.get('property_name')}
URL: {amber.get('url')}
Sections: {amber.get('sections_count')}
Total Items: {amber.get('total_items')}
Metrics: {json.dumps(amber.get('metrics', {}), indent=2)}
Sections Detail:
{json.dumps(amber.get('sections', []), indent=2)}

COMPETITOR DATA:
Property: {competitor.get('property_name')}
URL: {competitor.get('url')}
Sections: {competitor.get('sections_count')}
Total Items: {competitor.get('total_items')}
Metrics: {json.dumps(competitor.get('metrics', {}), indent=2)}
Sections Detail:
{json.dumps(competitor.get('sections', []), indent=2)}

COMPARISON RESULTS:
{json.dumps(comparison, indent=2)}{detailed_section}

Generate the complete markdown report following all required sections.
Use the ACTUAL numbers from the data provided above.
If detailed analysis is provided, use it to show ALL 21 sections in the Section Presence Matrix.
Be specific and actionable."""
    
    def _markdown_to_html(self, markdown: str) -> str:
        """
        Simple markdown to HTML conversion
        (Could use a library like markdown2 for better conversion)
        """
        html = markdown
        
        # Basic conversions
        html = html.replace('# ', '<h1>').replace('\n\n', '</h1>\n\n')
        html = html.replace('## ', '<h2>').replace('\n\n', '</h2>\n\n')
        html = html.replace('### ', '<h3>').replace('\n\n', '</h3>\n\n')
        html = html.replace('\n\n', '</p><p>')
        html = html.replace('- ', '<li>').replace('\n', '</li>\n')
        
        # Wrap in basic HTML structure
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Property Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""
        return html

