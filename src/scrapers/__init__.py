"""
Scraping modules for extracting property data from URLs
"""

# Lazy import to avoid firecrawl dependency when not needed
try:
    from .firecrawl_scraper import FirecrawlScraper
    __all__ = ["FirecrawlScraper"]
except ImportError:
    # FirecrawlScraper not available (firecrawl not installed)
    __all__ = []

