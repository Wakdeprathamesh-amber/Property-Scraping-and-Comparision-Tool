"""
Simple 4-Agent Pipeline

Replaces all the complex parsers, extractors, and multi-layer architecture.

Flow:
1. Raw text → LLM Extractor → Structured data
2. Structured data → LLM Comparator → Basic comparison
3. Detailed section analysis → Quantitative metrics
4. All data → LLM Reporter → Report
"""

from typing import Dict, Any
from src.agents.simple_extractor import SimpleLLMExtractor
from src.agents.simple_comparator import SimpleLLMComparator
from src.agents.detailed_analyzer import DetailedSectionAnalyzer
from src.agents.simple_reporter import SimpleLLMReporter
from src.utils.logger import setup_logger


class SimpleComparisonPipeline:
    """
    Simple pipeline that uses LLMs end-to-end
    
    No parsers, no canonical formats, no complexity.
    Just: Raw Text → LLM → Structured Output
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.extractor = SimpleLLMExtractor()
        self.comparator = SimpleLLMComparator()
        self.analyzer = DetailedSectionAnalyzer()
        self.reporter = SimpleLLMReporter()
    
    async def run(
        self,
        amber_raw: Dict[str, Any],
        competitor_raw: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run complete comparison pipeline
        
        Args:
            amber_raw: Raw data with 'extracted_content' containing text
            competitor_raw: Raw data with 'extracted_content' containing text
            
        Returns:
            Dict with:
            - amber_extracted
            - competitor_extracted
            - comparison
            - markdown_report
            - html_report
        """
        self.logger.info("=" * 60)
        self.logger.info("SIMPLE PIPELINE START (4 Agents)")
        self.logger.info("=" * 60)
        
        # Step 1: Extract from both properties
        self.logger.info("\n[Step 1/4] Extracting Amber data...")
        amber_extracted = self.extractor.extract(amber_raw)
        
        self.logger.info("\n[Step 1/4] Extracting Competitor data...")
        competitor_extracted = self.extractor.extract(competitor_raw)
        
        # Step 2: Basic comparison
        self.logger.info("\n[Step 2/4] Comparing properties (basic)...")
        comparison = self.comparator.compare(amber_extracted, competitor_extracted)
        
        # Step 3: Detailed section analysis (NEW - for all 21 sections)
        self.logger.info("\n[Step 3/4] Analyzing all 21 sections (detailed)...")
        detailed_analysis = self.analyzer.analyze(
            amber_extracted,
            competitor_extracted,
            comparison
        )
        
        # Step 4: Generate report
        self.logger.info("\n[Step 4/4] Generating report...")
        reports = self.reporter.generate_report(
            amber_extracted,
            competitor_extracted,
            comparison,
            detailed_analysis  # Pass detailed analysis
        )
        
        self.logger.info("=" * 60)
        self.logger.info("SIMPLE PIPELINE COMPLETE")
        self.logger.info(f"Amber: {amber_extracted.get('sections_count')} sections")
        self.logger.info(f"Competitor: {competitor_extracted.get('sections_count')} sections")
        self.logger.info(f"Detailed analysis: {len(detailed_analysis.get('all_21_sections', {}))} sections")
        self.logger.info(f"Report: {len(reports['markdown'])} chars")
        self.logger.info("=" * 60)
        
        return {
            "amber_extracted": amber_extracted,
            "competitor_extracted": competitor_extracted,
            "comparison": comparison,
            "detailed_analysis": detailed_analysis,  # Include detailed analysis
            "markdown_report": reports["markdown"],
            "html_report": reports["html"],
            "status": "completed"
        }


# Convenience function for backend
async def run_simple_comparison(
    amber_data: Dict[str, Any],
    competitor_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run simple comparison pipeline
    
    This replaces the complex workflow with 3 LLM calls
    """
    pipeline = SimpleComparisonPipeline()
    return await pipeline.run(amber_data, competitor_data)

