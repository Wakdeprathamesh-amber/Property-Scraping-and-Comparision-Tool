"""Data models for final comparison results"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Recommendation(BaseModel):
    """A single actionable recommendation"""
    priority: str = Field(description="high, medium, low")
    category: str = Field(description="content, seo, ux, marketing, media")
    section: Optional[str] = Field(default=None, description="Related section")
    action: str = Field(description="Specific action to take")
    rationale: str = Field(description="Why this matters")
    example: Optional[str] = Field(default=None, description="Example from competitor")
    estimated_impact: Optional[str] = Field(default=None, description="Expected impact")


class Insight(BaseModel):
    """A key insight from the comparison"""
    type: str = Field(description="strength, weakness, opportunity, threat")
    platform: str = Field(description="amber or competitor")
    category: str = Field(description="content, seo, ux, marketing")
    description: str
    evidence: Optional[List[str]] = Field(default=None, description="Supporting evidence")


class ComparisonResult(BaseModel):
    """Complete comparison result"""
    
    # Metadata
    property_name: str
    amber_url: str
    competitor_url: str
    competitor_name: Optional[str] = None
    comparison_date: datetime = Field(default_factory=datetime.now)
    
    # Section comparison
    sections_compared: List[str] = Field(default_factory=list)
    section_comparisons: Dict[str, Any] = Field(default_factory=dict)
    
    # Overall metrics
    overall_similarity_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1.01,  # Allow slight float precision tolerance
        description="Overall content similarity (0-1)"
    )
    amber_richness_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )
    competitor_richness_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )
    
    # Content metrics
    amber_total_word_count: Optional[int] = None
    competitor_total_word_count: Optional[int] = None
    amber_image_count: Optional[int] = None
    competitor_image_count: Optional[int] = None
    amber_video_count: Optional[int] = None
    competitor_video_count: Optional[int] = None
    
    # Sections analysis
    common_sections: List[str] = Field(default_factory=list)
    amber_unique_sections: List[str] = Field(default_factory=list)
    competitor_unique_sections: List[str] = Field(default_factory=list)
    missing_in_amber: List[str] = Field(default_factory=list)
    
    # Unmapped sections (sections that don't fit the 21 standard categories)
    unmapped_sections_amber: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    unmapped_sections_competitor: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    # Insights
    insights: List[Insight] = Field(default_factory=list)
    amber_strengths: List[str] = Field(default_factory=list)
    competitor_strengths: List[str] = Field(default_factory=list)
    
    # Recommendations
    recommendations: List[Recommendation] = Field(default_factory=list)
    
    # Summary
    executive_summary: Optional[str] = None
    overall_verdict: Optional[str] = None
    
    # Raw agent outputs (for debugging)
    agent_outputs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw outputs from each agent"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

