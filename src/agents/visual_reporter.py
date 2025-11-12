"""
Visual Report Generator - Professional UI for Property Comparison

Generates beautiful, industry-standard comparison reports with:
- Modern design
- Color-coded metrics
- Visual charts and progress bars
- Responsive layout
- Professional styling
"""

from typing import Dict, Any
import json
from src.utils.logger import setup_logger


class VisualReportGenerator:
    """
    Generates visually stunning HTML reports
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    def generate_html_report(
        self,
        amber_data: Dict[str, Any],
        competitor_data: Dict[str, Any],
        comparison: Dict[str, Any],
        markdown_report: str,
        detailed_analysis: Dict[str, Any] = None
    ) -> str:
        """
        Generate beautiful HTML report with modern UI
        
        Args:
            detailed_analysis: Optional detailed analysis with all 21 sections
        """
        self.logger.info("Generating visual HTML report")
        
        # Extract data
        amber_metrics = amber_data.get("metrics", {})
        competitor_metrics = competitor_data.get("metrics", {})
        
        # Build HTML
        html = self._build_html_structure(
            amber_data,
            competitor_data,
            comparison,
            amber_metrics,
            competitor_metrics,
            markdown_report,
            detailed_analysis  # Pass detailed analysis
        )
        
        return html
    
    def _build_html_structure(
        self,
        amber_data: Dict,
        competitor_data: Dict,
        comparison: Dict,
        amber_metrics: Dict,
        competitor_metrics: Dict,
        markdown_content: str,
        detailed_analysis: Dict = None
    ) -> str:
        """Build complete HTML structure with modern design"""
        
        amber_name = amber_data.get('property_name', 'Amber Property')
        comp_name = competitor_data.get('property_name', 'Competitor')
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Comparison Report - {amber_name} vs {comp_name}</title>
    <style>
        {self._get_modern_css()}
    </style>
</head>
<body>
    <div class="report-container">
        {self._generate_header(amber_data, competitor_data)}
        {self._generate_executive_summary(amber_data, competitor_data, comparison, detailed_analysis) if detailed_analysis else ""}
        {self._generate_score_cards(amber_data, competitor_data, comparison)}
        {self._generate_metrics_comparison(amber_metrics, competitor_metrics, amber_name, comp_name)}
        {self._generate_all_21_sections_table(detailed_analysis) if detailed_analysis else self._generate_section_presence(amber_data, competitor_data, comparison)}
        {self._generate_granular_comparison(detailed_analysis) if detailed_analysis else ""}
        {self._generate_detailed_section_breakdown(detailed_analysis) if detailed_analysis else ""}
        {self._generate_competitive_analysis(comparison)}
        {self._generate_recommendations(markdown_content)}
        {self._generate_footer()}
    </div>
    
    <script>
        {self._get_interactive_js()}
    </script>
</body>
</html>"""
    
    def _get_modern_css(self) -> str:
        """Modern CSS styling"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #2d3748;
            line-height: 1.6;
        }
        
        .report-container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        /* Header */
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        
        .report-header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .report-header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .report-header .date {
            margin-top: 10px;
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        /* Download Button */
        .download-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .download-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .download-btn:active {
            transform: translateY(0);
        }
        
        .download-btn svg {
            transition: transform 0.3s ease;
        }
        
        .download-btn:hover svg {
            transform: translateY(2px);
        }
        
        /* Floating Download Button for Mobile */
        @media (max-width: 768px) {
            .download-btn {
                position: fixed;
                bottom: 20px;
                right: 20px;
                top: auto;
                padding: 15px;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                z-index: 1000;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                justify-content: center;
            }
            
            .download-btn span {
                display: none;
            }
        }
        
        /* Score Cards */
        .score-section {
            padding: 40px;
            background: #f7fafc;
        }
        
        .score-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .score-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 4px solid;
        }
        
        .score-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }
        
        .score-card.amber {
            border-left-color: #667eea;
        }
        
        .score-card.competitor {
            border-left-color: #f56565;
        }
        
        .score-card.similarity {
            border-left-color: #48bb78;
        }
        
        .score-card .label {
            font-size: 0.85rem;
            text-transform: uppercase;
            color: #718096;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .score-card .value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2d3748;
        }
        
        .score-card .subtitle-text {
            font-size: 0.9rem;
            color: #a0aec0;
            margin-top: 5px;
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 1s ease;
        }
        
        /* Metrics Comparison */
        .metrics-section {
            padding: 40px;
        }
        
        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 25px;
            color: #2d3748;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .metric-item {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }
        
        .metric-name {
            font-size: 0.9rem;
            color: #718096;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .metric-comparison {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .metric-bar {
            flex: 1;
            height: 30px;
            background: #f7fafc;
            border-radius: 8px;
            position: relative;
            overflow: hidden;
        }
        
        .metric-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.85rem;
            transition: width 0.6s ease;
        }
        
        .metric-bar-fill.competitor {
            background: linear-gradient(90deg, #fc8181 0%, #f56565 100%);
        }
        
        .metric-value {
            font-size: 1.2rem;
            font-weight: 700;
            min-width: 40px;
            text-align: right;
        }
        
        /* Section Presence Table */
        .table-section {
            padding: 40px;
            background: #f7fafc;
        }
        
        .comparison-table {
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        
        .comparison-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .comparison-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
        }
        
        .comparison-table tbody tr {
            border-bottom: 1px solid #e2e8f0;
            transition: background 0.2s;
        }
        
        .comparison-table tbody tr:hover {
            background: #f7fafc;
        }
        
        .comparison-table td {
            padding: 15px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .status-badge.present {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-badge.missing {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .status-badge.amber-advantage {
            background: #bee3f8;
            color: #2c5282;
        }
        
        .status-badge.competitor-advantage {
            background: #feebc8;
            color: #7c2d12;
        }
        
        /* Competitive Analysis */
        .analysis-section {
            padding: 40px;
        }
        
        .analysis-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .analysis-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            border-top: 4px solid;
        }
        
        .analysis-card.advantages {
            border-top-color: #48bb78;
        }
        
        .analysis-card.gaps {
            border-top-color: #f56565;
        }
        
        .analysis-card.opportunities {
            border-top-color: #ed8936;
        }
        
        .analysis-card h3 {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #2d3748;
        }
        
        .analysis-card ul {
            list-style: none;
            padding: 0;
        }
        
        .analysis-card li {
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .analysis-card li:last-child {
            border-bottom: none;
        }
        
        .analysis-card li::before {
            content: '•';
            font-size: 1.5rem;
            color: #667eea;
            flex-shrink: 0;
        }
        
        /* Recommendations */
        .recommendations-section {
            padding: 40px;
            background: #f7fafc;
        }
        
        .recommendation-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid #ed8936;
            transition: transform 0.2s;
        }
        
        .recommendation-card:hover {
            transform: translateX(5px);
        }
        
        .recommendation-card .priority {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .recommendation-card .priority.high {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .recommendation-card .priority.medium {
            background: #feebc8;
            color: #7c2d12;
        }
        
        .recommendation-card .priority.low {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .recommendation-card h4 {
            font-size: 1.1rem;
            margin-bottom: 10px;
            color: #2d3748;
        }
        
        .recommendation-card p {
            color: #4a5568;
            font-size: 0.95rem;
        }
        
        /* Footer */
        .report-footer {
            padding: 30px 40px;
            background: #2d3748;
            color: white;
            text-align: center;
        }
        
        .report-footer p {
            opacity: 0.8;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .report-header h1 {
                font-size: 1.8rem;
            }
            
            .score-cards,
            .metrics-grid,
            .analysis-cards {
                grid-template-columns: 1fr;
            }
            
            body {
                padding: 10px;
            }
            
            .report-container {
                border-radius: 10px;
            }
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .score-card,
        .metric-item,
        .analysis-card {
            animation: slideIn 0.5s ease forwards;
        }
        
        /* Detailed Section Breakdown */
        .detailed-breakdown {
            padding: 40px;
            background: #f7fafc;
        }
        
        .breakdown-category {
            margin: 30px 0;
        }
        
        .breakdown-category h3 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .section-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .section-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .section-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .section-card.both {
            border-left-color: #4299e1;
        }
        
        .section-card.amber {
            border-left-color: #48bb78;
        }
        
        .section-card.competitor {
            border-left-color: #f56565;
        }
        
        .section-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #edf2f7;
        }
        
        .section-card-header h4 {
            font-size: 1.1rem;
            color: #2d3748;
            margin: 0;
        }
        
        .richness-badges {
            display: flex;
            gap: 8px;
        }
        
        .richness-badges .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .badge.amber {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .badge.competitor {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .metrics-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 10px 0;
        }
        
        .metric {
            font-size: 0.9rem;
            color: #4a5568;
            padding: 8px;
            background: #f7fafc;
            border-radius: 6px;
        }
        
        .gap-alert {
            background: #fff5f5;
            border: 1px solid #fc8181;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
            font-size: 0.9rem;
            color: #742a2a;
        }
        
        .advantage-note {
            background: #f0fff4;
            border: 1px solid #68d391;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
            font-size: 0.9rem;
            color: #22543d;
        }
        
        .verdict {
            margin: 15px 0;
            padding: 12px;
            background: #edf2f7;
            border-radius: 8px;
            font-size: 0.95rem;
            color: #2d3748;
            font-style: italic;
        }
        
        .recommendations {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
        }
        
        .recommendations strong {
            color: #2d3748;
            display: block;
            margin-bottom: 8px;
        }
        
        .recommendations ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .recommendations li {
            padding: 6px 0;
            padding-left: 20px;
            position: relative;
            font-size: 0.9rem;
            color: #4a5568;
        }
        
        .recommendations li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #4299e1;
            font-weight: bold;
        }
        
        /* Quantitative Summary */
        .quantitative-summary {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        
        .quantitative-summary h3 {
            font-size: 1.4rem;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
        }
        
        .summary-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .summary-label {
            font-size: 0.9rem;
            opacity: 0.95;
        }
        
        /* Legend */
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
            padding: 15px;
            background: #edf2f7;
            border-radius: 10px;
        }
        
        .legend span {
            font-size: 0.95rem;
            color: #4a5568;
            font-weight: 600;
        }
        
        /* Status cells and badges */
        .status-cell.present {
            color: #22543d;
            background: #c6f6d5;
            font-weight: 700;
        }
        
        .status-cell.missing {
            color: #742a2a;
            background: #fed7d7;
            font-weight: 700;
        }
        
        .status-badge {
            font-weight: 600;
            font-size: 0.95rem;
        }
        
        .score-cell {
            font-weight: 700;
            color: #4299e1;
        }
        
        .section-name {
            font-weight: 600;
            color: #2d3748;
        }
        
        /* Responsive design for section cards */
        @media (max-width: 768px) {
            .section-cards {
                grid-template-columns: 1fr;
            }
            
            .metrics-row {
                grid-template-columns: 1fr;
            }
            
            .summary-grid {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        /* Executive Summary */
        .executive-summary {
            background: white;
            padding: 40px;
            margin: 20px 0;
            border-bottom: 3px solid #e2e8f0;
        }
        
        .executive-summary h2 {
            font-size: 2rem;
            color: #2d3748;
            margin-bottom: 20px;
        }
        
        .summary-verdict {
            font-size: 1.5rem;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
            font-weight: 600;
        }
        
        .summary-verdict.positive {
            background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
            color: #22543d;
            border: 2px solid #48bb78;
        }
        
        .summary-verdict.warning {
            background: linear-gradient(135deg, #fed7d7 0%, #fc8181 100%);
            color: #742a2a;
            border: 2px solid #f56565;
        }
        
        .summary-verdict.neutral {
            background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%);
            color: #2c5282;
            border: 2px solid #4299e1;
        }
        
        .summary-grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }
        
        .summary-box {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .summary-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        
        .summary-icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        
        .summary-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 15px;
        }
        
        .summary-stat {
            font-size: 1rem;
            color: #2d3748;
            margin: 10px 0;
        }
        
        .big-number {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
        }
        
        .summary-detail {
            font-size: 0.85rem;
            color: #718096;
            margin-top: 10px;
        }
        
        .key-findings {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }
        
        .finding-column {
            background: #f7fafc;
            padding: 25px;
            border-radius: 12px;
        }
        
        .finding-column h3 {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #2d3748;
        }
        
        .finding-column ul {
            list-style: none;
            padding: 0;
        }
        
        .finding-column li {
            padding: 10px;
            margin: 8px 0;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #4299e1;
        }
        
        /* Granular Comparison */
        .granular-comparison-container {
            background: white;
            padding: 40px;
            margin: 30px 0;
        }
        
        .granular-comparison-container h2 {
            font-size: 1.8rem;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .info-box {
            background: #edf2f7;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 0.95rem;
            color: #4a5568;
        }
        
        .legend-item {
            margin: 0 10px;
            font-weight: 600;
        }
        
        .granular-section {
            background: #f7fafc;
            border-radius: 15px;
            padding: 30px;
            margin: 25px 0;
            border: 2px solid #e2e8f0;
        }
        
        .granular-header h3 {
            font-size: 1.4rem;
            color: #2d3748;
            margin-bottom: 20px;
        }
        
        .granular-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }
        
        .stat-pill {
            background: white;
            padding: 10px 20px;
            border-radius: 20px;
            border: 2px solid #e2e8f0;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .stat-label {
            font-size: 0.85rem;
            color: #718096;
        }
        
        .stat-value {
            font-size: 1.1rem;
            font-weight: 700;
            color: #4299e1;
        }
        
        .comparison-columns {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        
        .item-list {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #e2e8f0;
        }
        
        .item-list h4 {
            font-size: 1.1rem;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #edf2f7;
        }
        
        .item-list ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .item-list li {
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 6px;
            font-size: 0.95rem;
        }
        
        .common-item {
            background: #edf2f7;
            color: #4a5568;
        }
        
        .unique-item {
            background: #e6fffa;
            color: #234e52;
            border-left: 3px solid #38b2ac;
            font-weight: 600;
        }
        
        .more-items {
            background: #feebc8;
            color: #7c2d12;
            font-style: italic;
        }
        
        .gap-box {
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            border-left: 5px solid;
        }
        
        .gap-box.warning {
            background: #fff5f5;
            border-left-color: #f56565;
            color: #742a2a;
        }
        
        .gap-box.success {
            background: #f0fff4;
            border-left-color: #48bb78;
            color: #22543d;
        }
        
        .gap-box strong {
            display: block;
            margin-bottom: 10px;
            font-size: 1.05rem;
        }
        
        .gap-box p {
            margin: 10px 0;
            line-height: 1.6;
        }
        
        .action-note {
            margin-top: 12px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 6px;
            font-style: italic;
            font-size: 0.9rem;
        }
        
        /* Improved 21 Sections Table */
        .section-table {
            background: white;
            padding: 40px;
            margin: 30px 0;
        }
        
        .section-table h2 {
            font-size: 1.8rem;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .section-table .subtitle {
            color: #718096;
            font-size: 1rem;
            margin-bottom: 25px;
        }
        
        .modern-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        
        .modern-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .modern-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95rem;
        }
        
        .modern-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .modern-table tbody tr {
            transition: background 0.2s;
        }
        
        .modern-table tbody tr:hover {
            background: #f7fafc;
        }
        
        .modern-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        /* Responsive for new sections */
        @media (max-width: 768px) {
            .summary-grid-3 {
                grid-template-columns: 1fr;
            }
            
            .key-findings {
                grid-template-columns: 1fr;
            }
            
            .comparison-columns {
                grid-template-columns: 1fr;
            }
            
            .granular-stats {
                flex-direction: column;
            }
            
            .stat-pill {
                width: 100%;
                justify-content: space-between;
            }
        }
        """
    
    def _generate_header(self, amber_data: Dict, competitor_data: Dict) -> str:
        """Generate report header with download button"""
        from datetime import datetime
        
        amber_name = amber_data.get('property_name', 'Amber Property')
        competitor_name = competitor_data.get('property_name', 'Competitor')
        
        # Create safe filename
        safe_amber = amber_name.replace(' ', '_').replace('/', '_')[:30]
        filename = f"comparison_report_{safe_amber}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        return f"""
        <div class="report-header">
            <button class="download-btn" onclick="downloadReport('{filename}')" title="Download Report">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>Download Report</span>
            </button>
            <h1>🏠 Property Comparison Report</h1>
            <div class="subtitle">
                <strong>{amber_name}</strong> vs 
                <strong>{competitor_name}</strong>
            </div>
            <div class="date">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>
        """
    
    def _generate_executive_summary(
        self, 
        amber_data: Dict, 
        competitor_data: Dict, 
        comparison: Dict,
        detailed_analysis: Dict
    ) -> str:
        """Generate executive summary at the top"""
        if not detailed_analysis:
            return ""
        
        quant_summary = detailed_analysis.get('quantitative_summary', {})
        all_sections = detailed_analysis.get('all_21_sections', {})
        
        # Calculate key metrics
        total_amber = quant_summary.get('total_sections_amber', 0)
        total_comp = quant_summary.get('total_sections_competitor', 0)
        in_both = quant_summary.get('sections_in_both', 0)
        amber_only = quant_summary.get('amber_only', 0)
        comp_only = quant_summary.get('competitor_only', 0)
        neither = quant_summary.get('neither', 0)
        
        amber_avg = quant_summary.get('amber_avg_richness', 0)
        comp_avg = quant_summary.get('competitor_avg_richness', 0)
        
        # Determine verdict
        if amber_avg > comp_avg + 10:
            verdict = "🏆 <strong>Amber Leads</strong> with superior content richness"
            verdict_class = "positive"
        elif comp_avg > amber_avg + 10:
            verdict = "⚠️ <strong>Competitor Leads</strong> - improvements needed"
            verdict_class = "warning"
        else:
            verdict = "⚖️ <strong>Competitive Parity</strong> - neck and neck"
            verdict_class = "neutral"
        
        # Top 3 strengths and gaps
        strengths = []
        gaps = []
        
        for section_key, section_data in all_sections.items():
            status = section_data.get('status', '')
            amber_score = section_data.get('amber_metrics', {}).get('richness_score', 0)
            comp_score = section_data.get('competitor_metrics', {}).get('richness_score', 0)
            section_name = section_key.replace('_', ' ').title()
            
            if status == 'amber_only' or (status == 'both_have' and amber_score > comp_score + 20):
                strengths.append(f"<strong>{section_name}</strong> ({amber_score}/100)")
            elif status == 'competitor_only' or (status == 'both_have' and comp_score > amber_score + 20):
                gaps.append(f"<strong>{section_name}</strong> ({comp_score}/100 vs {amber_score}/100)")
        
        strengths_html = "".join([f"<li>✅ {s}</li>" for s in strengths[:3]]) or "<li>No significant advantages</li>"
        gaps_html = "".join([f"<li>⚠️ {g}</li>" for g in gaps[:3]]) or "<li>No critical gaps</li>"
        
        return f"""
        <div class="executive-summary">
            <h2>📋 Executive Summary</h2>
            <div class="summary-verdict {verdict_class}">
                {verdict}
            </div>
            
            <div class="summary-grid-3">
                <div class="summary-box">
                    <div class="summary-icon">📊</div>
                    <div class="summary-title">Coverage</div>
                    <div class="summary-stat">
                        <span class="big-number">{total_amber}</span> / 21 Amber<br>
                        <span class="big-number">{total_comp}</span> / 21 Competitor
                    </div>
                    <div class="summary-detail">{in_both} shared, {amber_only} Amber exclusive, {comp_only} Competitor exclusive</div>
                </div>
                
                <div class="summary-box">
                    <div class="summary-icon">⭐</div>
                    <div class="summary-title">Quality</div>
                    <div class="summary-stat">
                        Amber: <span class="big-number">{amber_avg:.1f}</span>/100<br>
                        Competitor: <span class="big-number">{comp_avg:.1f}</span>/100
                    </div>
                    <div class="summary-detail">Average richness across all sections</div>
                </div>
                
                <div class="summary-box">
                    <div class="summary-icon">🎯</div>
                    <div class="summary-title">Opportunity</div>
                    <div class="summary-stat">
                        <span class="big-number">{comp_only + neither}</span> sections<br>
                        to add or improve
                    </div>
                    <div class="summary-detail">{comp_only} competitor-only, {neither} missing in both</div>
                </div>
            </div>
            
            <div class="key-findings">
                <div class="finding-column">
                    <h3>🏆 Top Strengths</h3>
                    <ul>{strengths_html}</ul>
                </div>
                <div class="finding-column">
                    <h3>⚠️ Critical Gaps</h3>
                    <ul>{gaps_html}</ul>
                </div>
            </div>
        </div>
        """
    
    def _generate_score_cards(self, amber_data: Dict, competitor_data: Dict, comparison: Dict) -> str:
        """Generate score cards"""
        amber_sections = amber_data.get('sections_count', 0)
        competitor_sections = competitor_data.get('sections_count', 0)
        similarity = comparison.get('overall_similarity', 0) * 100
        
        amber_metrics = amber_data.get('metrics', {})
        competitor_metrics = competitor_data.get('metrics', {})
        
        amber_score = min(100, (amber_sections * 5) + sum(amber_metrics.values()))
        competitor_score = min(100, (competitor_sections * 5) + sum(competitor_metrics.values()))
        
        return f"""
        <div class="score-section">
            <h2 class="section-title">📊 Overall Scores</h2>
            <div class="score-cards">
                <div class="score-card amber">
                    <div class="label">Amber Score</div>
                    <div class="value">{amber_score}<span style="font-size:1.5rem;color:#a0aec0;">/100</span></div>
                    <div class="subtitle-text">{amber_sections} sections | {amber_data.get('total_items', 0)} items</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {amber_score}%"></div>
                    </div>
                </div>
                
                <div class="score-card competitor">
                    <div class="label">{competitor_data.get('property_name', 'Competitor')} Score</div>
                    <div class="value">{competitor_score}<span style="font-size:1.5rem;color:#a0aec0;">/100</span></div>
                    <div class="subtitle-text">{competitor_sections} sections | {competitor_data.get('total_items', 0)} items</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {competitor_score}%; background: linear-gradient(90deg, #fc8181 0%, #f56565 100%);"></div>
                    </div>
                </div>
                
                <div class="score-card similarity">
                    <div class="label">Content Similarity</div>
                    <div class="value">{similarity:.1f}<span style="font-size:1.5rem;color:#a0aec0;">%</span></div>
                    <div class="subtitle-text">How similar the listings are</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {similarity}%; background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_metrics_comparison(self, amber_metrics: Dict, competitor_metrics: Dict, amber_name: str = "Amber", comp_name: str = "Competitor") -> str:
        """Generate metrics comparison with visual bars"""
        metrics_html = ""
        
        metric_names = {
            'amenities_count': 'Amenities',
            'room_types_count': 'Room Types',
            'faqs_count': 'FAQs',
            'bills_included_count': 'Bills Included',
            'payment_options_count': 'Payment Options',
            'universities_mentioned': 'Universities',
            'pois_count': 'Nearby POIs',
            'reviews_count': 'Reviews',
            'trust_badges_count': 'Trust Badges',
            'safety_features_count': 'Safety Features'
        }
        
        for key, name in metric_names.items():
            amber_val = amber_metrics.get(key, 0)
            competitor_val = competitor_metrics.get(key, 0)
            
            max_val = max(amber_val, competitor_val, 1)
            amber_pct = (amber_val / max_val) * 100 if max_val > 0 else 0
            comp_pct = (competitor_val / max_val) * 100 if max_val > 0 else 0
            
            metrics_html += f"""
            <div class="metric-item">
                <div class="metric-name">{name}</div>
                <div class="metric-comparison">
                    <div style="flex: 1;">
                        <div style="font-size: 0.75rem; color: #718096; margin-bottom: 5px;">{amber_name[:20]}</div>
                        <div class="metric-bar">
                            <div class="metric-bar-fill" style="width: {amber_pct}%">
                                {amber_val if amber_pct > 20 else ''}
                            </div>
                        </div>
                    </div>
                    <div class="metric-value" style="color: #667eea;">{amber_val}</div>
                </div>
                <div class="metric-comparison" style="margin-top: 10px;">
                    <div style="flex: 1;">
                        <div style="font-size: 0.75rem; color: #718096; margin-bottom: 5px;">{comp_name[:20]}</div>
                        <div class="metric-bar">
                            <div class="metric-bar-fill competitor" style="width: {comp_pct}%">
                                {competitor_val if comp_pct > 20 else ''}
                            </div>
                        </div>
                    </div>
                    <div class="metric-value" style="color: #f56565;">{competitor_val}</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="metrics-section">
            <h2 class="section-title">📈 Detailed Metrics Comparison</h2>
            <div class="metrics-grid">
                {metrics_html}
            </div>
        </div>
        """
    
    def _generate_section_presence(self, amber_data: Dict, competitor_data: Dict, comparison: Dict) -> str:
        """Generate section presence table"""
        amber_sections = {s['name']: s for s in amber_data.get('sections', [])}
        competitor_sections = {s['name']: s for s in competitor_data.get('sections', [])}
        
        all_sections = set(list(amber_sections.keys()) + list(competitor_sections.keys()))
        
        rows_html = ""
        for section in sorted(all_sections):
            amber_present = section in amber_sections
            comp_present = section in competitor_sections
            
            amber_badge = '<span class="status-badge present">✓ Present</span>' if amber_present else '<span class="status-badge missing">✗ Missing</span>'
            comp_badge = '<span class="status-badge present">✓ Present</span>' if comp_present else '<span class="status-badge missing">✗ Missing</span>'
            
            if amber_present and not comp_present:
                status = '<span class="status-badge amber-advantage">🏆 Amber Advantage</span>'
            elif comp_present and not amber_present:
                status = '<span class="status-badge competitor-advantage">🚨 Gap Identified</span>'
            elif amber_present and comp_present:
                status = '<span class="status-badge present">⚖️ Both Have</span>'
            else:
                status = '<span class="status-badge missing">❌ Both Missing</span>'
            
            rows_html += f"""
            <tr>
                <td><strong>{section.replace('_', ' ').title()}</strong></td>
                <td>{amber_badge}</td>
                <td>{comp_badge}</td>
                <td>{status}</td>
            </tr>
            """
        
        return f"""
        <div class="table-section">
            <h2 class="section-title">📋 Section Presence Matrix</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Section</th>
                        <th>Amber</th>
                        <th>Competitor</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_all_21_sections_table(self, detailed_analysis: Dict) -> str:
        """Generate comprehensive table showing ALL 21 standard sections"""
        if not detailed_analysis or 'all_21_sections' not in detailed_analysis:
            return self._generate_section_presence({}, {}, {})
        
        all_sections = detailed_analysis['all_21_sections']
        
        rows_html = ""
        for section_key, section_data in all_sections.items():
            # Format section name
            section_name = section_key.replace('_', ' ').title()
            
            # Get status
            status = section_data.get('status', 'neither')
            status_icon = section_data.get('status_icon', '❌')
            
            # Amber status
            amber_icon = "✓" if section_data.get('amber_present') else "✗"
            amber_class = "present" if section_data.get('amber_present') else "missing"
            
            # Competitor status
            comp_icon = "✓" if section_data.get('competitor_present') else "✗"
            comp_class = "present" if section_data.get('competitor_present') else "missing"
            
            # Status description
            status_text = {
                'both_have': 'Both Have',
                'amber_only': 'Amber Only',
                'competitor_only': 'Competitor Only',
                'neither': 'Neither'
            }.get(status, status)
            
            # Richness scores
            amber_score = section_data.get('amber_metrics', {}).get('richness_score', 0)
            comp_score = section_data.get('competitor_metrics', {}).get('richness_score', 0)
            
            rows_html += f"""
            <tr>
                <td class="section-name">{section_name}</td>
                <td class="status-cell {amber_class}">{amber_icon}</td>
                <td class="status-cell {comp_class}">{comp_icon}</td>
                <td class="status-badge">{status_icon} {status_text}</td>
                <td class="score-cell">{amber_score}/100</td>
                <td class="score-cell">{comp_score}/100</td>
            </tr>
            """
        
        return f"""
        <div class="section-table">
            <h2>📋 All 21 Standard Sections - Comprehensive Matrix</h2>
            <p class="subtitle">Complete analysis of all industry-standard property listing sections</p>
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>Section</th>
                        <th>Amber</th>
                        <th>Competitor</th>
                        <th>Status</th>
                        <th>Amber Score</th>
                        <th>Comp Score</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            <div class="legend">
                <span>⚖️ Both Have</span>
                <span>🏆 Amber Only</span>
                <span>🚨 Competitor Only</span>
                <span>❌ Neither</span>
            </div>
        </div>
        """
    
    def _generate_granular_comparison(self, detailed_analysis: Dict) -> str:
        """Generate item-level granular comparison for key sections"""
        if not detailed_analysis or 'all_21_sections' not in detailed_analysis:
            return ""
        
        all_sections = detailed_analysis['all_21_sections']
        
        # Focus on key sections for granular comparison
        key_sections = ['amenities', 'faqs', 'room_types', 'bills_included', 'property_overview']
        
        granular_html = ""
        
        for section_key in key_sections:
            if section_key not in all_sections:
                continue
            
            section_data = all_sections[section_key]
            if section_data.get('status') == 'neither':
                continue
            
            section_name = section_key.replace('_', ' ').title()
            
            amber_items = section_data.get('amber_metrics', {}).get('specific_items', [])
            comp_items = section_data.get('competitor_metrics', {}).get('specific_items', [])
            missing_in_amber = section_data.get('gap_analysis', {}).get('missing_in_amber', [])
            missing_in_comp = section_data.get('gap_analysis', {}).get('missing_in_competitor', [])
            
            # Skip if no items to compare
            if not amber_items and not comp_items:
                continue
            
            # Create comparison table
            amber_items_html = ""
            comp_items_html = ""
            missing_amber_html = ""
            missing_comp_html = ""
            
            if amber_items:
                amber_items_html = "<div class='item-list'><h4>✅ In Amber:</h4><ul>"
                for item in amber_items[:10]:  # Limit to 10
                    in_comp = item in comp_items
                    amber_items_html += f"<li class='{'common-item' if in_comp else 'unique-item'}'>{item} {'' if in_comp else '🏆'}</li>"
                if len(amber_items) > 10:
                    amber_items_html += f"<li class='more-items'>... +{len(amber_items) - 10} more</li>"
                amber_items_html += "</ul></div>"
            
            if comp_items:
                comp_items_html = "<div class='item-list'><h4>✅ In Competitor:</h4><ul>"
                for item in comp_items[:10]:
                    in_amber = item in amber_items
                    comp_items_html += f"<li class='{'common-item' if in_amber else 'unique-item'}'>{item} {'' if in_amber else '🚨'}</li>"
                if len(comp_items) > 10:
                    comp_items_html += f"<li class='more-items'>... +{len(comp_items) - 10} more</li>"
                comp_items_html += "</ul></div>"
            
            if missing_in_amber:
                missing_amber_html = f"""
                <div class='gap-box warning'>
                    <strong>⚠️ Missing in Amber ({len(missing_in_amber)} items):</strong>
                    <p>{', '.join(missing_in_amber[:5])}{f'... +{len(missing_in_amber) - 5} more' if len(missing_in_amber) > 5 else ''}</p>
                    <div class='action-note'>Action: Consider adding these to match competitor offering</div>
                </div>
                """
            
            if missing_in_comp:
                missing_comp_html = f"""
                <div class='gap-box success'>
                    <strong>🏆 Exclusive to Amber ({len(missing_in_comp)} items):</strong>
                    <p>{', '.join(missing_in_comp[:5])}{f'... +{len(missing_in_comp) - 5} more' if len(missing_in_comp) > 5 else ''}</p>
                    <div class='action-note'>Advantage: Highlight these unique offerings in marketing</div>
                </div>
                """
            
            # Summary stats
            total_unique_items = len(set(amber_items + comp_items))
            common_items_count = len(set(amber_items) & set(comp_items))
            overlap_percent = (common_items_count / total_unique_items * 100) if total_unique_items > 0 else 0
            
            stats_html = f"""
            <div class='granular-stats'>
                <div class='stat-pill'>
                    <span class='stat-label'>Total Unique Items:</span>
                    <span class='stat-value'>{total_unique_items}</span>
                </div>
                <div class='stat-pill'>
                    <span class='stat-label'>Common Items:</span>
                    <span class='stat-value'>{common_items_count}</span>
                </div>
                <div class='stat-pill'>
                    <span class='stat-label'>Overlap:</span>
                    <span class='stat-value'>{overlap_percent:.0f}%</span>
                </div>
                <div class='stat-pill'>
                    <span class='stat-label'>Amber Only:</span>
                    <span class='stat-value'>{len(missing_in_comp)}</span>
                </div>
                <div class='stat-pill'>
                    <span class='stat-label'>Comp Only:</span>
                    <span class='stat-value'>{len(missing_in_amber)}</span>
                </div>
            </div>
            """
            
            granular_html += f"""
            <div class='granular-section'>
                <div class='granular-header'>
                    <h3>🔍 {section_name} - Item-Level Comparison</h3>
                    {stats_html}
                </div>
                <div class='granular-content'>
                    <div class='comparison-columns'>
                        {amber_items_html}
                        {comp_items_html}
                    </div>
                    {missing_amber_html}
                    {missing_comp_html}
                </div>
            </div>
            """
        
        if not granular_html:
            return ""
        
        return f"""
        <div class='granular-comparison-container'>
            <h2>🔬 Granular Item-Level Comparison</h2>
            <p class="subtitle">Detailed side-by-side comparison of specific items in each section</p>
            <div class='info-box'>
                <strong>Legend:</strong> 
                <span class='legend-item'>Items present in both</span> | 
                <span class='legend-item'>🏆 Amber exclusive</span> | 
                <span class='legend-item'>🚨 Competitor exclusive</span>
            </div>
            {granular_html}
        </div>
        """
    
    def _generate_detailed_section_breakdown(self, detailed_analysis: Dict) -> str:
        """Generate detailed section-by-section quantitative breakdown"""
        if not detailed_analysis or 'all_21_sections' not in detailed_analysis:
            return ""
        
        all_sections = detailed_analysis['all_21_sections']
        quantitative_summary = detailed_analysis.get('quantitative_summary', {})
        
        sections_html = ""
        
        # Group sections by status
        both_have = []
        amber_only = []
        competitor_only = []
        
        for section_key, section_data in all_sections.items():
            status = section_data.get('status', 'neither')
            if status == 'both_have':
                both_have.append((section_key, section_data))
            elif status == 'amber_only':
                amber_only.append((section_key, section_data))
            elif status == 'competitor_only':
                competitor_only.append((section_key, section_data))
        
        # Generate cards for sections in both
        if both_have:
            sections_html += """
            <div class="breakdown-category">
                <h3>⚖️ Sections in Both Properties</h3>
                <div class="section-cards">
            """
            for section_key, section_data in both_have:
                sections_html += self._generate_section_card(section_key, section_data, 'both')
            sections_html += "</div></div>"
        
        # Generate cards for Amber-only sections
        if amber_only:
            sections_html += """
            <div class="breakdown-category">
                <h3>🏆 Amber Exclusive Sections</h3>
                <div class="section-cards">
            """
            for section_key, section_data in amber_only:
                sections_html += self._generate_section_card(section_key, section_data, 'amber')
            sections_html += "</div></div>"
        
        # Generate cards for Competitor-only sections
        if competitor_only:
            sections_html += """
            <div class="breakdown-category">
                <h3>🚨 Competitor Exclusive Sections</h3>
                <div class="section-cards">
            """
            for section_key, section_data in competitor_only:
                sections_html += self._generate_section_card(section_key, section_data, 'competitor')
            sections_html += "</div></div>"
        
        # Quantitative summary
        summary_html = f"""
        <div class="quantitative-summary">
            <h3>📊 Quantitative Summary</h3>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-value">{quantitative_summary.get('total_sections_amber', 0)}</div>
                    <div class="summary-label">Amber Sections</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{quantitative_summary.get('total_sections_competitor', 0)}</div>
                    <div class="summary-label">Competitor Sections</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{quantitative_summary.get('sections_in_both', 0)}</div>
                    <div class="summary-label">Sections in Both</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{quantitative_summary.get('amber_avg_richness', 0):.1f}/100</div>
                    <div class="summary-label">Amber Avg Richness</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{quantitative_summary.get('competitor_avg_richness', 0):.1f}/100</div>
                    <div class="summary-label">Competitor Avg Richness</div>
                </div>
            </div>
        </div>
        """
        
        return f"""
        <div class="detailed-breakdown">
            <h2>📊 Detailed Section-Specific Analysis</h2>
            <p class="subtitle">Quantitative metrics and gap analysis for each section</p>
            {summary_html}
            {sections_html}
        </div>
        """
    
    def _generate_section_card(self, section_key: str, section_data: Dict, card_type: str) -> str:
        """Generate a card for a single section"""
        section_name = section_key.replace('_', ' ').title()
        
        amber_metrics = section_data.get('amber_metrics', {})
        comp_metrics = section_data.get('competitor_metrics', {})
        
        amber_items = amber_metrics.get('specific_items', [])
        comp_items = comp_metrics.get('specific_items', [])
        
        gap_analysis = section_data.get('gap_analysis', {})
        missing_in_amber = gap_analysis.get('missing_in_amber', [])
        
        # Items HTML
        items_html = ""
        if card_type == 'both':
            items_html = f"""
            <div class="metrics-row">
                <div class="metric">
                    <strong>Amber:</strong> {amber_metrics.get('item_count', 0)} items, 
                    {amber_metrics.get('word_count', 0)} words
                </div>
                <div class="metric">
                    <strong>Competitor:</strong> {comp_metrics.get('item_count', 0)} items, 
                    {comp_metrics.get('word_count', 0)} words
                </div>
            </div>
            """
            if missing_in_amber:
                items_html += f"""
                <div class="gap-alert">
                    <strong>⚠️ Missing in Amber:</strong> {', '.join(missing_in_amber[:5])}
                    {f'... +{len(missing_in_amber) - 5} more' if len(missing_in_amber) > 5 else ''}
                </div>
                """
        elif card_type == 'amber':
            items_html = f"""
            <div class="metrics-row">
                <div class="metric">
                    <strong>Amber:</strong> {amber_metrics.get('item_count', 0)} items, 
                    {amber_metrics.get('word_count', 0)} words
                </div>
            </div>
            <div class="advantage-note">
                🏆 Competitive advantage - consider highlighting this
            </div>
            """
        else:  # competitor
            items_html = f"""
            <div class="metrics-row">
                <div class="metric">
                    <strong>Competitor:</strong> {comp_metrics.get('item_count', 0)} items, 
                    {comp_metrics.get('word_count', 0)} words
                </div>
            </div>
            <div class="gap-alert">
                🚨 Critical gap - recommend adding this section
            </div>
            """
        
        # Recommendations
        recommendations = section_data.get('recommendations', [])
        recs_html = ""
        if recommendations:
            recs_html = "<div class='recommendations'><strong>Actions:</strong><ul>"
            for rec in recommendations[:3]:
                recs_html += f"<li>{rec}</li>"
            recs_html += "</ul></div>"
        
        verdict = section_data.get('quantitative_verdict', 'No verdict')
        
        return f"""
        <div class="section-card {card_type}">
            <div class="section-card-header">
                <h4>{section_name}</h4>
                <div class="richness-badges">
                    <span class="badge amber">A: {amber_metrics.get('richness_score', 0)}/100</span>
                    <span class="badge competitor">C: {comp_metrics.get('richness_score', 0)}/100</span>
                </div>
            </div>
            {items_html}
            <div class="verdict">{verdict}</div>
            {recs_html}
        </div>
        """
    
    def _generate_competitive_analysis(self, comparison: Dict) -> str:
        """Generate competitive analysis cards"""
        amber_advantages = comparison.get('amber_advantages', [])
        comp_advantages = comparison.get('competitor_advantages', [])
        missing_in_amber = comparison.get('missing_in_amber', [])
        
        advantages_html = "".join([f"<li>{adv}</li>" for adv in amber_advantages[:5]]) or "<li>No specific advantages identified</li>"
        gaps_html = "".join([f"<li>{gap.replace('_', ' ').title()}</li>" for gap in missing_in_amber[:5]]) or "<li>No major gaps</li>"
        opportunities_html = "".join([f"<li>{adv}</li>" for adv in comp_advantages[:5]]) or "<li>Competitor has no unique advantages</li>"
        
        return f"""
        <div class="analysis-section">
            <h2 class="section-title">💡 Competitive Analysis</h2>
            <div class="analysis-cards">
                <div class="analysis-card advantages">
                    <h3>🏆 Amber Advantages</h3>
                    <ul>
                        {advantages_html}
                    </ul>
                </div>
                
                <div class="analysis-card gaps">
                    <h3>🚨 Gaps to Address</h3>
                    <ul>
                        {gaps_html}
                    </ul>
                </div>
                
                <div class="analysis-card opportunities">
                    <h3>🎯 Competitor Strengths</h3>
                    <ul>
                        {opportunities_html}
                    </ul>
                </div>
            </div>
        </div>
        """
    
    def _generate_recommendations(self, markdown_content: str) -> str:
        """Generate recommendations section"""
        # Extract recommendations from markdown
        import re
        
        recommendations = []
        
        # Look for action items in markdown
        action_pattern = r'Action:\s*(.+?)(?:\n|$)'
        actions = re.findall(action_pattern, markdown_content, re.IGNORECASE)
        
        for i, action in enumerate(actions[:10]):
            priority = 'high' if i < 3 else 'medium' if i < 7 else 'low'
            recommendations.append((priority, action.strip()))
        
        if not recommendations:
            recommendations = [
                ('high', 'Add reviews and ratings section to build trust'),
                ('high', 'Include trust badges and certifications'),
                ('medium', 'Expand FAQ section with more detailed answers'),
                ('medium', 'Add virtual tour or 360° images'),
                ('low', 'Include customer testimonials')
            ]
        
        recs_html = ""
        for priority, rec in recommendations:
            recs_html += f"""
            <div class="recommendation-card">
                <span class="priority {priority}">{priority.upper()}</span>
                <h4>{rec}</h4>
            </div>
            """
        
        return f"""
        <div class="recommendations-section">
            <h2 class="section-title">🎯 Actionable Recommendations</h2>
            {recs_html}
        </div>
        """
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        return """
        <div class="report-footer">
            <p>Generated by Property Comparison AI System</p>
            <p style="margin-top: 10px; font-size: 0.9rem;">
                Powered by Simple LLM Pipeline | Accurate • Fast • Reliable
            </p>
        </div>
        """
    
    def _get_interactive_js(self) -> str:
        """Add interactive JavaScript"""
        return """
        // Animate progress bars on load
        window.addEventListener('load', function() {
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
            
            const metricBars = document.querySelectorAll('.metric-bar-fill');
            metricBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 200);
            });
        });
        
        // Download Report Function
        function downloadReport(filename) {
            // Clone the entire document
            const htmlContent = document.documentElement.outerHTML;
            
            // Create blob
            const blob = new Blob([htmlContent], { type: 'text/html' });
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            
            // Trigger download
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Show success message
            showDownloadSuccess();
        }
        
        // Show download success notification
        function showDownloadSuccess() {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 10000;
                font-weight: 600;
                animation: slideIn 0.3s ease;
            `;
            notification.innerHTML = '✓ Report downloaded successfully!';
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => document.body.removeChild(notification), 300);
            }, 3000);
        }
        
        // Smooth scroll
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
        
        // Add animations for notifications
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
        """

