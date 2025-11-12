"""Data models for raw property data"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ImageData(BaseModel):
    """Image metadata"""
    url: str
    alt: Optional[str] = None
    title: Optional[str] = None


class LinkData(BaseModel):
    """Link metadata"""
    url: str
    text: Optional[str] = None
    type: Optional[str] = None  # internal, external, anchor


class MetaData(BaseModel):
    """SEO and meta information"""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    og_tags: Optional[Dict[str, str]] = None
    schema_org: Optional[Dict[str, Any]] = None


class ExtractedContent(BaseModel):
    """Extracted content from property page"""
    text: str = Field(description="Full visible text content")
    sections: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Pre-identified sections if available"
    )
    images: List[ImageData] = Field(default_factory=list)
    links: List[LinkData] = Field(default_factory=list)
    meta_tags: Optional[MetaData] = None
    videos: Optional[List[Dict[str, str]]] = Field(default=None)
    interactive_elements: Optional[List[str]] = Field(
        default=None,
        description="Dropdowns, tabs, modals, etc."
    )


class PropertyData(BaseModel):
    """Complete property data input"""
    property_name: str
    provider: Optional[str] = None
    url: str
    location: Optional[str] = None
    raw_html: Optional[str] = Field(
        default=None,
        description="Raw HTML if available"
    )
    extracted_content: ExtractedContent
    additional_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any additional scraped metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "property_name": "iQ Sterling Court",
                "provider": "IQ Student Accommodation",
                "url": "https://amberstudent.com/properties/iq-sterling-court",
                "location": "London, UK",
                "extracted_content": {
                    "text": "iQ Sterling Court is located in Wembley...",
                    "images": [
                        {"url": "https://...", "alt": "Bedroom"}
                    ],
                    "links": [],
                    "meta_tags": {
                        "title": "iQ Sterling Court | Student Accommodation"
                    }
                }
            }
        }


