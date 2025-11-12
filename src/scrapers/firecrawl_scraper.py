"""
Firecrawl Web Scraper

Uses Firecrawl API to scrape property websites and convert them to clean markdown.
Perfect for LLM processing - no complex parsing needed!
"""

import os
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from firecrawl import FirecrawlApp
from src.utils.logger import setup_logger


class FirecrawlScraper:
    """
    Scrapes property websites using Firecrawl API
    
    Returns clean markdown ready for LLM processing
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl scraper
        
        Args:
            api_key: Firecrawl API key (or set FIRECRAWL_API_KEY env var)
        """
        self.logger = setup_logger(self.__class__.__name__)
        
        # Get API key from env or parameter
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Firecrawl API key not found! "
                "Set FIRECRAWL_API_KEY environment variable or pass api_key parameter."
            )
        
        # Initialize Firecrawl client
        self.client = FirecrawlApp(api_key=self.api_key)
        self.logger.info("Firecrawl scraper initialized")
    
    def is_valid_url(self, text: str) -> bool:
        """
        Check if text is a valid URL
        
        Args:
            text: Input text to check
            
        Returns:
            True if valid URL, False otherwise
        """
        text = text.strip()
        
        # Quick check for URL-like patterns
        if not (text.startswith('http://') or text.startswith('https://') or text.startswith('www.')):
            return False
        
        # Parse URL
        try:
            result = urlparse(text if text.startswith('http') else f'https://{text}')
            return bool(result.netloc and result.scheme in ['http', 'https'])
        except Exception:
            return False
    
    def scrape_url(self, url: str, formats: list = None) -> Dict[str, Any]:
        """
        Scrape a URL using Firecrawl API
        
        Args:
            url: URL to scrape
            formats: List of formats to extract (default: ['markdown', 'html'])
            
        Returns:
            Dict with scraped data including markdown, metadata, images, links
        """
        if formats is None:
            formats = ['markdown', 'html']
        
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = f'https://{url}'
        
        self.logger.info(f"🔥 Scraping URL: {url}")
        
        try:
            # Call Firecrawl API
            scrape_result = self.client.scrape_url(
                url,
                params={
                    'formats': formats,
                    'onlyMainContent': True,  # Skip navigation, footer, ads
                    'waitFor': 2000,  # Wait for dynamic content to load
                    'timeout': 30000  # 30 second timeout
                }
            )
            
            # Extract data from response
            markdown = scrape_result.get('markdown', '')
            html = scrape_result.get('html', '')
            metadata = scrape_result.get('metadata', {})
            
            # Extract images and links from metadata
            images = []
            links = []
            
            # Firecrawl returns image URLs
            if metadata.get('images'):
                images = metadata['images']
            
            # Firecrawl returns link data
            if metadata.get('links'):
                links = metadata['links']
            
            # Get title and description
            title = metadata.get('title', 'Unknown Property')
            description = metadata.get('description', '')
            
            self.logger.info(
                f"✅ Scraped successfully: {len(markdown)} chars markdown, "
                f"{len(images)} images, {len(links)} links"
            )
            
            return {
                'success': True,
                'url': url,
                'markdown': markdown,
                'html': html,
                'metadata': {
                    'title': title,
                    'description': description,
                    'images': images,
                    'links': links,
                    'og_tags': metadata.get('ogTags', {}),
                    'language': metadata.get('language'),
                    'source_url': metadata.get('sourceURL', url)
                },
                'scraper': 'firecrawl'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def scrape_to_property_data(self, url: str) -> Dict[str, Any]:
        """
        Scrape URL and convert to property data format
        
        Returns format compatible with parse_markdown_to_property_data
        """
        result = self.scrape_url(url)
        
        if not result['success']:
            raise Exception(f"Scraping failed: {result.get('error', 'Unknown error')}")
        
        # Extract property name from title
        property_name = result['metadata']['title']
        
        # Clean up common suffixes from title
        for suffix in [' - Student Housing', ' - Property', ' | Amber Student', ' | UniversityLiving']:
            if suffix in property_name:
                property_name = property_name.split(suffix)[0]
        
        return {
            'property_name': property_name.strip(),
            'url': result['url'],
            'extracted_content': {
                'text': result['markdown'],
                'html': result.get('html'),
                'images': result['metadata'].get('images', []),
                'links': result['metadata'].get('links', [])
            },
            'metadata': result['metadata'],
            'scraper': 'firecrawl'
        }
    
    def scrape_multiple(self, urls: list) -> Dict[str, Dict[str, Any]]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dict mapping URLs to scraped data
        """
        results = {}
        for url in urls:
            self.logger.info(f"Scraping {url}...")
            results[url] = self.scrape_url(url)
        
        return results

