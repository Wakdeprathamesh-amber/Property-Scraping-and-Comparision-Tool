"""
Scraper Factory
Chooses the appropriate scraper based on platform and availability
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
from src.utils.logger import setup_logger

# Import scrapers
# Lazy import for FirecrawlScraper (optional dependency)
try:
    from src.scrapers.firecrawl_scraper import FirecrawlScraper
except ImportError:
    FirecrawlScraper = None  # Not available if firecrawl not installed

from src.scrapers.amber_api_scraper import AmberAPIScraper
from src.scrapers.uhomes_puppeteer_scraper import UHomesPuppeteerScraper


class ScraperFactory:
    """
    Factory to create and manage scrapers
    Automatically chooses best scraper based on platform
    """
    
    def __init__(self, prefer_api: bool = True, use_playwright: bool = False):
        """
        Initialize scraper factory
        
        Args:
            prefer_api: Prefer API scrapers over Firecrawl (default: True)
            use_playwright: Use Playwright for UHomes instead of Selenium (default: False)
        """
        self.logger = setup_logger(self.__class__.__name__)
        self.prefer_api = prefer_api
        self.use_playwright = use_playwright
        
        # Initialize scrapers (lazy loading)
        self._amber_api_scraper = None
        self._uhomes_puppeteer_scraper = None
        self._firecrawl_scraper = None
    
    def detect_platform(self, url: str) -> str:
        """
        Detect platform from URL
        
        Args:
            url: Property URL
            
        Returns:
            'amber' or 'uhomes' or 'unknown'
        """
        url_lower = url.lower()
        
        if 'amberstudent.com' in url_lower or 'amber' in url_lower:
            return 'amber'
        elif 'uhomes.com' in url_lower:
            return 'uhomes'
        else:
            return 'unknown'
    
    def get_amber_scraper(self, use_api: Optional[bool] = None) -> Any:
        """
        Get Amber scraper (API or Firecrawl)
        
        Args:
            use_api: Force API usage (None = use prefer_api setting)
            
        Returns:
            Amber scraper instance
        """
        use_api = use_api if use_api is not None else self.prefer_api
        
        if use_api:
            try:
                if self._amber_api_scraper is None:
                    self._amber_api_scraper = AmberAPIScraper()
                return self._amber_api_scraper
            except Exception as e:
                self.logger.warning(f"Amber API scraper failed, falling back to Firecrawl: {e}")
                # Fallback to Firecrawl
                return self.get_firecrawl_scraper()
        else:
            return self.get_firecrawl_scraper()
    
    def get_uhomes_scraper(self, use_puppeteer: Optional[bool] = None) -> Any:
        """
        Get UHomes scraper (Puppeteer or Firecrawl)
        
        Args:
            use_puppeteer: Force Puppeteer usage (None = use prefer_api setting)
            
        Returns:
            UHomes scraper instance
        """
        use_puppeteer = use_puppeteer if use_puppeteer is not None else self.prefer_api
        
        if use_puppeteer:
            try:
                if self._uhomes_puppeteer_scraper is None:
                    self._uhomes_puppeteer_scraper = UHomesPuppeteerScraper(use_playwright=self.use_playwright)
                return self._uhomes_puppeteer_scraper
            except Exception as e:
                self.logger.warning(f"UHomes Puppeteer scraper failed, falling back to Firecrawl: {e}")
                # Fallback to Firecrawl
                return self.get_firecrawl_scraper()
        else:
            return self.get_firecrawl_scraper()
    
    def get_firecrawl_scraper(self) -> FirecrawlScraper:
        """
        Get Firecrawl scraper (fallback option)
        
        Returns:
            Firecrawl scraper instance
            
        Raises:
            ImportError: If firecrawl package is not installed
            ValueError: If FIRECRAWL_API_KEY is not set
        """
        if FirecrawlScraper is None:
            raise ImportError("firecrawl package is not installed. Install it with: pip install firecrawl-py")
        if self._firecrawl_scraper is None:
            import os
            api_key = os.getenv('FIRECRAWL_API_KEY')
            if not api_key:
                raise ValueError("FIRECRAWL_API_KEY not found. Cannot use Firecrawl scraper.")
            self._firecrawl_scraper = FirecrawlScraper(api_key=api_key)
        return self._firecrawl_scraper
    
    def scrape_url(self, url: str, platform: Optional[str] = None, force_firecrawl: bool = False) -> Dict[str, Any]:
        """
        Scrape URL using appropriate scraper
        
        Args:
            url: Property URL
            platform: 'amber' or 'uhomes' (auto-detected if None)
            force_firecrawl: Force use of Firecrawl instead of API scrapers
            
        Returns:
            Scraped data dict
        """
        # Detect platform if not provided
        if platform is None:
            platform = self.detect_platform(url)
        
        if platform == 'amber':
            if force_firecrawl:
                scraper = self.get_firecrawl_scraper()
            else:
                scraper = self.get_amber_scraper()
        elif platform == 'uhomes':
            if force_firecrawl:
                scraper = self.get_firecrawl_scraper()
            else:
                scraper = self.get_uhomes_scraper()
        else:
            # Unknown platform, use Firecrawl
            self.logger.warning(f"Unknown platform for {url}, using Firecrawl")
            scraper = self.get_firecrawl_scraper()
        
        # Scrape
        result = scraper.scrape_url(url)
        
        # Add platform info
        result['platform'] = platform
        result['scraper_used'] = result.get('scraper', 'unknown')
        
        return result


if __name__ == "__main__":
    # Test factory
    factory = ScraperFactory(prefer_api=True)
    
    # Test Amber
    amber_url = "https://amberstudent.com/places/ben-russell-court-leicester-1608300341147"
    print(f"\nTesting Amber scraper: {amber_url}")
    result = factory.scrape_url(amber_url)
    print(f"Success: {result['success']}, Scraper: {result.get('scraper_used')}")
    
    # Test UHomes
    uhomes_url = "https://en.uhomes.com/uk/aberdeen/detail-apartments-530876"
    print(f"\nTesting UHomes scraper: {uhomes_url}")
    result = factory.scrape_url(uhomes_url)
    print(f"Success: {result['success']}, Scraper: {result.get('scraper_used')}")


