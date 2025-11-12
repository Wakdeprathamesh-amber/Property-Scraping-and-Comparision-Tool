"""Data models for sections and their analysis"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Section(BaseModel):
    """A single section extracted from property page"""
    section_name: str = Field(description="Normalized section name (e.g., 'overview', 'rooms', 'amenities')")
    original_heading: Optional[str] = Field(default=None, description="Original heading text from page")
    content: str = Field(description="Text content of the section")
    word_count: int = Field(default=0)
    subsections: Optional[List[Dict[str, Any]]] = Field(default=None)
    images: Optional[List[str]] = Field(default=None, description="Image URLs in this section")
    links: Optional[List[str]] = Field(default=None, description="Links in this section")
    tags: Optional[List[str]] = Field(default=None, description="Tags or badges in this section")
    
    # Enhanced granular extraction
    headers: Optional[List[str]] = Field(
        default_factory=list,
        description="All headers/subheadings within this section"
    )
    items: Optional[List[str]] = Field(
        default_factory=list,
        description="Itemized list (amenities, FAQs, room types, features, etc.)"
    )
    structured_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Structured data: pricing details, discounts, offers, config, tenancy terms"
    )
    bullet_points: Optional[List[str]] = Field(
        default_factory=list,
        description="All bullet points or list items"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "section_name": "amenities",
                "original_heading": "Features & Amenities",
                "content": "WiFi, Laundry Facility, Common Area...",
                "word_count": 42,
                "tags": ["Bills Included", "24/7 Security"]
            }
        }


class AnalyzedSection(BaseModel):
    """Section with analysis results"""
    section: Section
    
    # Quantitative metrics
    richness_score: float = Field(ge=0, le=100, description="Content richness score (0-100)")
    completeness_score: float = Field(ge=0, le=100, description="Completeness score (0-100)")
    detail_level: str = Field(description="basic, moderate, detailed, comprehensive")
    
    # Qualitative analysis
    tone: str = Field(description="factual, promotional, emotional, technical")
    key_themes: List[str] = Field(default_factory=list, description="Main topics covered")
    seo_keywords: List[str] = Field(default_factory=list, description="Important SEO keywords")
    
    # Content characteristics
    has_pricing: bool = Field(default=False)
    has_contact_info: bool = Field(default=False)
    has_cta: bool = Field(default=False, description="Has call-to-action")
    
    # Summary
    summary: Optional[str] = Field(default=None, description="AI-generated summary")
    strengths: Optional[List[str]] = Field(default=None)
    weaknesses: Optional[List[str]] = Field(default=None)
    
    # Enhanced granular analysis
    item_count: Optional[int] = Field(
        default=None,
        description="Total number of items (amenities, FAQs, room types, etc.)"
    )
    items_detail: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Detailed breakdown of each item with metadata"
    )
    headers_found: Optional[List[str]] = Field(
        default_factory=list,
        description="All headers/subheadings found in this section"
    )
    content_structure: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Structure analysis: lists, tables, paragraphs, images per subsection"
    )
    # Section-specific analysis
    quantitative_metrics: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Section-specific quantitative metrics (counts, prices, distances, etc.)"
    )
    gaps_vs_industry: Optional[List[str]] = Field(
        default_factory=list,
        description="Gaps compared to industry standards/best-in-class competitors"
    )
    actionables: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Actionable recommendations by department (marketing/seo/product)"
    )


class SectionComparison(BaseModel):
    """Comparison of a section between Amber and competitor"""
    section_name: str
    
    # Presence
    present_in_amber: bool
    present_in_competitor: bool
    
    # Content comparison
    amber_word_count: Optional[int] = None
    competitor_word_count: Optional[int] = None
    word_count_diff: Optional[int] = None
    
    # Quality comparison
    amber_richness: Optional[float] = None
    competitor_richness: Optional[float] = None
    
    # Text similarity
    text_similarity: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Cosine similarity (0-1)"
    )
    
    # Content gaps
    unique_in_amber: Optional[List[str]] = Field(
        default=None,
        description="Points present only in Amber"
    )
    unique_in_competitor: Optional[List[str]] = Field(
        default=None,
        description="Points present only in competitor"
    )
    
    # Winner
    winner: Optional[str] = Field(
        default=None,
        description="amber, competitor, or tie"
    )
    verdict: Optional[str] = Field(
        default=None,
        description="Brief verdict explanation"
    )
    
    # Enhanced granular comparison
    amber_item_count: Optional[int] = Field(
        default=None,
        description="Number of items in Amber (e.g., 12 amenities)"
    )
    competitor_item_count: Optional[int] = Field(
        default=None,
        description="Number of items in Competitor (e.g., 16 amenities)"
    )
    amber_items: Optional[List[str]] = Field(
        default_factory=list,
        description="Complete list of all items in Amber's section"
    )
    competitor_items: Optional[List[str]] = Field(
        default_factory=list,
        description="Complete list of all items in Competitor's section"
    )
    missing_in_amber: Optional[List[str]] = Field(
        default_factory=list,
        description="Items in competitor but missing in Amber"
    )
    extra_in_amber: Optional[List[str]] = Field(
        default_factory=list,
        description="Items in Amber but not in competitor"
    )
    common_items: Optional[List[str]] = Field(
        default_factory=list,
        description="Items present in both"
    )
    amber_headers: Optional[List[str]] = Field(
        default_factory=list,
        description="Headers/subheadings in Amber's section"
    )
    competitor_headers: Optional[List[str]] = Field(
        default_factory=list,
        description="Headers/subheadings in Competitor's section"
    )
    amber_images: Optional[int] = Field(
        default=None,
        description="Number of images in this section for Amber"
    )
    competitor_images: Optional[int] = Field(
        default=None,
        description="Number of images in this section for Competitor"
    )
    detailed_diff: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Detailed differences: pricing, discounts, offers, config, tenancy, room details"
    )
    gaps_vs_industry_amber: Optional[List[str]] = Field(
        default_factory=list,
        description="Gaps vs industry standards for Amber's section"
    )
    gaps_vs_industry_competitor: Optional[List[str]] = Field(
        default_factory=list,
        description="Gaps vs industry standards for Competitor's section"
    )
    actionables_amber: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Actionable recommendations for Amber by department"
    )
    actionables_competitor: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Actionable recommendations for Competitor by department"
    )

