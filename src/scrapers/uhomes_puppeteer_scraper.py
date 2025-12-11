"""
UHomes Puppeteer Scraper
Uses Selenium/Playwright to extract structured data from UHomes pages
Extracts window.__NUXT__ data (Nuxt.js app state) for accurate data
"""

import json
import re
import time
from typing import Dict, Any, Optional, List
from html.parser import HTMLParser
from src.utils.logger import setup_logger

# Try to import Selenium first, fallback to Playwright
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class LinkExtractor(HTMLParser):
    """Extract links from HTML content"""
    def __init__(self):
        super().__init__()
        self.links = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self.links.append(attr_value)


class UHomesPuppeteerScraper:
    """
    Scrapes UHomes properties using browser automation
    Extracts window.__NUXT__ data for structured JSON
    """
    
    def __init__(self, use_playwright: bool = False):
        """
        Initialize UHomes scraper
        
        Args:
            use_playwright: Use Playwright instead of Selenium (default: False, uses Selenium)
        """
        self.logger = setup_logger(self.__class__.__name__)
        self.use_playwright = use_playwright
        
        # Check available libraries
        if use_playwright:
            if not PLAYWRIGHT_AVAILABLE:
                raise ImportError("Playwright not installed. Install with: pip install playwright && playwright install")
            self.logger.info("UHomes Puppeteer scraper initialized (Playwright)")
        else:
            if not SELENIUM_AVAILABLE:
                raise ImportError("Selenium not installed. Install with: pip install selenium")
            self.logger.info("UHomes Puppeteer scraper initialized (Selenium)")
    
    def extract_nuxt_data_selenium(self, url: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Extract window.__NUXT__ data using Selenium with retry logic
        
        Args:
            url: UHomes property URL
            max_retries: Maximum number of retry attempts
            
        Returns:
            Extracted hData from window.__NUXT__
        """
        for attempt in range(max_retries + 1):
            driver = None
            try:
                # Setup Chrome options
                chrome_options = Options()
                chrome_options.add_argument('--headless=new')  # Use new headless mode
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # Try to use system Chrome if available (macOS)
                import platform
                if platform.system() == 'Darwin':  # macOS
                    chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                
                # Create driver with service
                from selenium.webdriver.chrome.service import Service
                service = Service()
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(90)  # Increased timeout
                driver.implicitly_wait(10)
                
                self.logger.info(f"Loading page: {url}")
                
                # Navigate to page
                driver.get(url)
                
                # Wait for page to be ready
                time.sleep(3)  # Give page time to start loading
                
                # Wait for page to load and JavaScript to execute
                wait = WebDriverWait(driver, 60)  # Increased wait time
                
                # Try multiple strategies to wait for __NUXT__
                try:
                    wait.until(lambda d: d.execute_script('return typeof window.__NUXT__ !== "undefined"'))
                except TimeoutException:
                    # Try waiting for document ready
                    wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    # Give extra time for JavaScript
                    time.sleep(5)
                    # Check again
                    if not driver.execute_script('return typeof window.__NUXT__ !== "undefined"'):
                        raise Exception("__NUXT__ not found after extended wait")
                
                # Wait for dynamic content to load (FAQs, etc.)
                # Scroll to bottom to trigger lazy loading
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for content to load
                    # Scroll back to top
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                except:
                    pass  # Ignore scroll errors
                
                # Wait for FAQ section to potentially load
                # Check if FAQ elements exist in DOM
                try:
                    # Wait a bit more for any lazy-loaded content
                    time.sleep(3)
                except:
                    pass
                
                # Try to extract FAQs from DOM if not in __NUXT__
                # UHomes uses div.faq-item structure
                faqs_from_dom = driver.execute_script('''
                    try {
                        const faqs = [];
                        
                        // Method 1: Look for div.faq-item elements (UHomes structure)
                        const faqItems = document.querySelectorAll('div.faq-item');
                        faqItems.forEach(item => {
                            // Try to find question and answer within the item
                            // Questions might be in strong, b, or first line
                            // Answers might be in p, div, or rest of text
                            const text = item.innerText || item.textContent || '';
                            if (text.trim()) {
                                // Split by newlines - first line is usually question
                                const lines = text.split('\\n').filter(l => l.trim());
                                if (lines.length >= 2) {
                                    // First line is question, rest is answer
                                    const question = lines[0].trim();
                                    const answer = lines.slice(1).join(' ').trim();
                                    if (question && answer) {
                                        faqs.push({
                                            question: question,
                                            answer: answer
                                        });
                                    }
                                } else if (lines.length === 1) {
                                    // Single line - might be question only or combined
                                    // Try to split by common patterns
                                    const parts = lines[0].split(/[?]|[:]/);
                                    if (parts.length >= 2) {
                                        faqs.push({
                                            question: parts[0].trim() + '?',
                                            answer: parts.slice(1).join(' ').trim()
                                        });
                                    }
                                }
                            }
                            
                            // Also try structured approach
                            const questionEl = item.querySelector('strong, b, [class*="question"], [class*="title"]');
                            const answerEl = item.querySelector('p, div, [class*="answer"], [class*="content"]');
                            if (questionEl && answerEl) {
                                const q = questionEl.textContent.trim();
                                const a = answerEl.textContent.trim();
                                if (q && a && !faqs.find(f => f.question === q)) {
                                    faqs.push({ question: q, answer: a });
                                }
                            }
                        });
                        
                        // Method 2: Look for FAQ container and extract items
                        const faqContainers = document.querySelectorAll('[class*="faq"], [id*="faq"]');
                        faqContainers.forEach(container => {
                            const items = container.querySelectorAll('div.faq-item, [class*="faq-item"]');
                            items.forEach(item => {
                                const text = item.innerText || item.textContent || '';
                                if (text.trim()) {
                                    const lines = text.split('\\n').filter(l => l.trim());
                                    if (lines.length >= 2) {
                                        const question = lines[0].trim();
                                        const answer = lines.slice(1).join(' ').trim();
                                        if (question && answer && !faqs.find(f => f.question === question)) {
                                            faqs.push({ question: question, answer: answer });
                                        }
                                    }
                                }
                            });
                        });
                        
                        // Remove duplicates
                        const uniqueFaqs = [];
                        const seenQuestions = new Set();
                        faqs.forEach(faq => {
                            const qKey = faq.question.toLowerCase().trim();
                            if (!seenQuestions.has(qKey)) {
                                seenQuestions.add(qKey);
                                uniqueFaqs.push(faq);
                            }
                        });
                        
                        return uniqueFaqs.length > 0 ? uniqueFaqs : null;
                    } catch(e) {
                        console.error('FAQ extraction error:', e);
                        return null;
                    }
                ''')
                
                # Extract __NUXT__ data - serialize to JSON in JavaScript to avoid circular reference issues
                nuxt_json = driver.execute_script('''
                    if (typeof window.__NUXT__ === 'undefined') {
                        return null;
                    }
                    try {
                        return JSON.stringify(window.__NUXT__);
                    } catch(e) {
                        // If stringify fails, try to extract just the data we need
                        if (window.__NUXT__.data && window.__NUXT__.data[0] && window.__NUXT__.data[0].hData) {
                            return JSON.stringify(window.__NUXT__.data[0].hData);
                        }
                        return null;
                    }
                ''')
                
                if not nuxt_json:
                    raise Exception("__NUXT__ data not found or could not be serialized")
                
                # Parse JSON
                nuxt_data = json.loads(nuxt_json)
                
                # Handle different JSON structures
                if isinstance(nuxt_data, dict):
                    # If we got hData directly, use it
                    if 'house' in nuxt_data or 'about' in nuxt_data:
                        h_data = nuxt_data
                    # Otherwise extract from full structure
                    elif 'data' in nuxt_data and nuxt_data.get('data'):
                        if isinstance(nuxt_data['data'], list) and len(nuxt_data['data']) > 0:
                            h_data = nuxt_data['data'][0].get('hData', {})
                        else:
                            h_data = nuxt_data.get('data', {})
                    else:
                        h_data = nuxt_data
                elif isinstance(nuxt_data, list) and len(nuxt_data) > 0:
                    # If it's a list, get first item
                    if isinstance(nuxt_data[0], dict) and 'hData' in nuxt_data[0]:
                        h_data = nuxt_data[0]['hData']
                    else:
                        h_data = nuxt_data[0] if isinstance(nuxt_data[0], dict) else {}
                else:
                    raise Exception("Unexpected __NUXT__ data structure")
                
                if not h_data or (isinstance(h_data, dict) and len(h_data) == 0):
                    raise Exception("hData not found or empty in __NUXT__")
                
                # Add FAQs from DOM if found and not in __NUXT__ data
                if faqs_from_dom and len(faqs_from_dom) > 0:
                    if 'faq' not in h_data or not h_data.get('faq'):
                        h_data['faq'] = faqs_from_dom
                        self.logger.info(f"✅ Extracted {len(faqs_from_dom)} FAQs from DOM")
                
                self.logger.info("✅ Successfully extracted __NUXT__ data")
                return h_data
                
            except (TimeoutException, WebDriverException) as e:
                if attempt < max_retries:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(5)  # Wait before retry
                    continue
                else:
                    raise Exception(f"Failed after {max_retries + 1} attempts: {e}")
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(5)
                    continue
                else:
                    raise
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass  # Ignore errors when closing
    
    def extract_nuxt_data_playwright(self, url: str) -> Dict[str, Any]:
        """
        Extract window.__NUXT__ data using Playwright
        
        Args:
            url: UHomes property URL
            
        Returns:
            Extracted hData from window.__NUXT__
        """
        with sync_playwright() as p:
            try:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                self.logger.info(f"Loading page: {url}")
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for __NUXT__ to be available
                page.wait_for_function('typeof window.__NUXT__ !== "undefined"', timeout=30000)
                
                # Extract __NUXT__ data
                nuxt_data = page.evaluate('window.__NUXT__')
                
                if not nuxt_data or not nuxt_data.get('data'):
                    raise Exception("__NUXT__ data not found or empty")
                
                # Extract hData
                h_data = nuxt_data['data'][0].get('hData', {})
                
                if not h_data:
                    raise Exception("hData not found in __NUXT__")
                
                self.logger.info("✅ Successfully extracted __NUXT__ data")
                return h_data
                
            finally:
                browser.close()
    
    def extract_links_from_html(self, html_content: str) -> List[str]:
        """Extract all links from HTML content"""
        if not html_content:
            return []
        
        extractor = LinkExtractor()
        try:
            extractor.feed(html_content)
            return extractor.links
        except Exception as e:
            self.logger.warning(f"Error extracting links from HTML: {e}")
            return []
    
    def extract_hero_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hero section features from UHomes data"""
        switch = data.get('switch', {})
        house = data.get('house', {})
        location = data.get('location', {})
        room_types = data.get('room_types', {})
        
        # Check for VR links in room types
        has_360_tour = False
        vr_link_count = 0
        room_type_items = room_types.get('room_type_items', [])
        for room_item in room_type_items:
            media = room_item.get('media', {})
            meta = media.get('meta', {})
            if meta.get('vr_link_count', 0) > 0:
                has_360_tour = True
                vr_link_count += meta.get('vr_link_count', 0)
        
        # Count videos from media array and digital_human_videos
        video_count = 0
        media_array = data.get('media', [])
        for media_item in media_array:
            if media_item.get('type') == 'video':
                video_count += media_item.get('count', 0)
        
        digital_videos = data.get('tips', {}).get('digital_human_videos', {})
        if digital_videos and digital_videos.get('items'):
            video_count += len(digital_videos.get('items', []))
        
        features = {
            'has_360_tour': has_360_tour,
            'has_3d_tour': False,   # Not directly available in structure
            'has_video_tour': bool(switch.get('is_has_video', 0)) or video_count > 0,
            'has_live_video_tour': bool(switch.get('is_live_video_tour', 0)),
            'has_map': bool(house.get('staticmap_image')),
            'has_map_toggle': bool(house.get('staticmap_image')),  # Assume toggle if map exists
            'has_street_view': bool(location.get('street_view_lat') and location.get('street_view_lng')),
            'has_price_display': bool(house.get('rent_amount')),
            'video_count': video_count,
            'vr_link_count': vr_link_count,
            'on_site_video': bool(switch.get('on_site_video', 0))
        }
        
        return features
    
    def extract_videos(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract video information from UHomes data"""
        videos = []
        
        # Extract from digital_human_videos
        digital_videos = data.get('tips', {}).get('digital_human_videos', {})
        if digital_videos and digital_videos.get('items'):
            for item in digital_videos.get('items', []):
                videos.append({
                    'url': item.get('video_url', ''),
                    'thumbnail_url': item.get('thumb_url', ''),
                    'duration': item.get('duration', ''),
                    'type': 'digital_human_video',
                    'caption': 'Digital Human Video'
                })
        
        # Extract from media array (videos)
        media_array = data.get('media', [])
        for media_item in media_array:
            if media_item.get('type') == 'video' and media_item.get('items'):
                for video_item in media_item.get('items', []):
                    video_data = video_item.get('media_video', {}) or video_item
                    videos.append({
                        'url': video_data.get('video_url', '') or video_data.get('url', ''),
                        'thumbnail_url': video_data.get('thumb_url', '') or video_data.get('thumbnail_url', ''),
                        'duration': video_data.get('duration', ''),
                        'type': 'property_video',
                        'caption': video_data.get('caption', 'Property Video')
                    })
        
        # Extract from room types (if videos exist in room type media)
        room_types = data.get('room_types', {}).get('room_type_items', [])
        for room_type in room_types:
            media = room_type.get('media', {})
            video_items = media.get('video', [])
            if video_items:
                for video_item in video_items:
                    video_data = video_item.get('media_video', {}) or video_item
                    videos.append({
                        'url': video_data.get('video_url', '') or video_data.get('url', ''),
                        'thumbnail_url': video_data.get('thumb_url', '') or video_data.get('thumbnail_url', ''),
                        'duration': video_data.get('duration', ''),
                        'type': 'room_type_video',
                        'caption': f"Room Type Video - {room_type.get('room_type', {}).get('name', 'Unknown')}"
                    })
        
        return videos
    
    def extract_payment_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed payment information from UHomes data"""
        fees = data.get('fees', {})
        house = data.get('house', {})
        installment_data = data.get('installment', [])
        tips = data.get('tips', {})
        
        payment_details = {
            'installment_options': [],
            'payment_methods': [],
            'guarantor_required': False,
            'holding_fee': None,
            'deposit': None,
            'other_fees': []
        }
        
        # Extract installment options
        if installment_data:
            for inst in installment_data:
                inst_count = inst.get('installment_count', 0)
                if inst_count > 0 and inst_count not in payment_details['installment_options']:
                    payment_details['installment_options'].append(inst_count)
                # Check guarantor requirement
                if inst.get('guarantor', 0) > 0:
                    payment_details['guarantor_required'] = True
        
        # Extract from house.installment_count (if available)
        if house.get('installment_count', 0) > 0:
            if house.get('installment_count') not in payment_details['installment_options']:
                payment_details['installment_options'].append(house.get('installment_count'))
        
        # Extract payment methods
        payment_method_ids = house.get('payment_method', [])
        # Map payment method IDs (would need mapping, but store IDs for now)
        payment_details['payment_method_ids'] = payment_method_ids
        
        # Extract deposit from fees
        if fees.get('deposit'):
            deposit = fees['deposit'].get('amount', {})
            if deposit:
                payment_details['deposit'] = {
                    'amount': deposit.get('amount', ''),
                    'currency': deposit.get('abbr', '£'),
                    'tips': fees['deposit'].get('tips', ''),
                    'payment_time': fees['deposit'].get('payment_time', '')
                }
        
        # Extract other fees
        other_fees = fees.get('other_fees', [])
        for fee in other_fees:
            fee_amount = fee.get('amount', {})
            payment_details['other_fees'].append({
                'title': fee.get('title', ''),
                'amount': fee_amount.get('amount', '') if isinstance(fee_amount, dict) else '',
                'currency': fee_amount.get('abbr', '£') if isinstance(fee_amount, dict) else '£',
                'tips': fee.get('tips', ''),
                'payment_time': fee.get('payment_time', '')
            })
        
        # Extract holding fee from cancellation policy text (if mentioned)
        installment_remind = tips.get('installment_remind', '')
        if installment_remind:
            payment_details['installment_reminder'] = installment_remind
        
        return payment_details
    
    def extract_offers_details(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed offers information"""
        offers = []
        
        # Extract from promotion array
        promotions = data.get('promotion', [])
        for promo in promotions:
            offers.append({
                'name': promo.get('title', ''),
                'description': promo.get('description', ''),
                'type': 'promotion'
            })
        
        # Extract from tips.media_bottom (exclusive offers)
        tips = data.get('tips', {})
        media_bottom = tips.get('media_bottom', [])
        for offer in media_bottom:
            offer_amount = offer.get('offer_amount', {})
            offers.append({
                'name': offer.get('desc', 'Exclusive Offer'),
                'description': f"Up to {offer_amount.get('abbr', '£')}{offer_amount.get('amount', '')}",
                'amount': offer_amount.get('amount', ''),
                'currency': offer_amount.get('abbr', '£'),
                'type': offer.get('type', 'exclusive_offer'),
                'expired_time': offer.get('expired_time'),
                'remain_time': offer.get('remain_time')
            })
        
        # Check for exclusive offer flag
        switch = data.get('switch', {})
        if switch.get('is_exclusive_offer', 0) > 0:
            # Add exclusive offer indicator
            offers.append({
                'name': 'Exclusive Offer',
                'description': 'This property has exclusive offers available only through UHomes',
                'type': 'exclusive_offer_flag'
            })
        
        return offers
    
    def extract_room_types(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed room types from room_types.room_type_items"""
        room_types_data = data.get('room_types', {})
        room_type_items = room_types_data.get('room_type_items', [])
        
        room_types = []
        for item in room_type_items:
            room_type = item.get('room_type', {})
            media = item.get('media', {})
            media_meta = media.get('meta', {})
            
            room_data = {
                'name': room_type.get('name', ''),
                'type_id': room_type.get('type_id', ''),
                'sku': room_type.get('sku', ''),
                'price': room_type.get('rent_amount', {}).get('amount', ''),
                'currency': room_type.get('rent_amount', {}).get('abbr', '£'),
                'promo_price': room_type.get('promo_price', {}).get('amount', ''),
                'area_sqm': room_type.get('area_sqm', {}),
                'area_sqft': room_type.get('area_sqft', {}),
                'bed_count': room_type.get('bed_count', ''),
                'bathroom_count': room_type.get('bathroom_count', ''),
                'kitchen_type': room_type.get('kitchen_type', ''),
                'booking_status': room_type.get('booking_status', ''),
                'image_count': media_meta.get('image_count', 0),
                'video_count': media_meta.get('video_count', 0),
                'vr_link_count': media_meta.get('vr_link_count', 0),
                'has_360_tour': media_meta.get('vr_link_count', 0) > 0,
                'images': [img.get('media_img', {}).get('path', '') for img in media.get('image', [])]
            }
            room_types.append(room_data)
        
        return room_types
    
    def extract_virtual_tours(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract 360° virtual tour information from room types"""
        virtual_tours = []
        
        room_types_data = data.get('room_types', {})
        room_type_items = room_types_data.get('room_type_items', [])
        
        for item in room_type_items:
            media = item.get('media', {})
            media_meta = media.get('meta', {})
            room_type = item.get('room_type', {})
            
            if media_meta.get('vr_link_count', 0) > 0:
                # VR links exist but URLs might be in different structure
                # Check for VR link data
                vr_links = media.get('vr_link', []) or []
                for vr_link in vr_links:
                    virtual_tours.append({
                        'url': vr_link.get('url', '') or vr_link.get('link', ''),
                        'type': '360_tour',
                        'room_type': room_type.get('name', 'Unknown'),
                        'is_360_tour': True
                    })
        
        return virtual_tours
    
    def extract_all_media(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all media from media array (images, videos, etc.)"""
        media_array = data.get('media', [])
        
        all_images = []
        all_videos = []
        
        for media_item in media_array:
            media_type = media_item.get('type', '')
            items = media_item.get('items', [])
            
            if media_type == 'image':
                for img_item in items:
                    media_img = img_item.get('media_img', {})
                    all_images.append({
                        'url': media_img.get('path', ''),
                        'media_id': media_img.get('media_id', ''),
                        'type': img_item.get('source', ''),
                        'group': img_item.get('group', '')
                    })
            elif media_type == 'video':
                for video_item in items:
                    media_video = video_item.get('media_video', {}) or video_item
                    all_videos.append({
                        'url': media_video.get('video_url', '') or media_video.get('url', ''),
                        'thumbnail_url': media_video.get('thumb_url', '') or media_video.get('thumbnail_url', ''),
                        'type': 'media_video',
                        'caption': media_video.get('caption', 'Property Video')
                    })
        
        return {
            'images': all_images,
            'videos': all_videos,
            'total_images': len(all_images),
            'total_videos': len(all_videos)
        }
    
    def extract_nearby_properties(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract nearby/similar properties if available"""
        # Check if UHomes has nearby properties in data
        nearby = data.get('nearby_properties', [])
        if not nearby:
            # Check tips for recommendations
            tips = data.get('tips', {})
            nearby = tips.get('similar_properties', [])
        
        properties = []
        for prop in nearby:
            properties.append({
                'name': prop.get('name') or prop.get('title', ''),
                'url': prop.get('url', ''),
                'distance': prop.get('distance', ''),
                'price': prop.get('price', '')
            })
        
        return properties
    
    def json_to_markdown(self, data: Dict[str, Any], platform: str = 'uhomes') -> str:
        """
        Convert UHomes JSON data to markdown format
        Compatible with existing analysis pipeline
        
        Args:
            data: hData from window.__NUXT__
            
        Returns:
            Markdown string
        """
        markdown_parts = []
        
        # Property Name
        property_name = data.get('house', {}).get('title', 'Unknown Property')
        markdown_parts.append(f"# {property_name}\n")
        
        # Hero & Media Section
        hero_features = self.extract_hero_features(data)
        markdown_parts.append(f"\n## Hero & Media\n\n")
        markdown_parts.append(f"**Media Features:**\n")
        if hero_features['has_video_tour']:
            markdown_parts.append(f"- ✅ Video Tour Available\n")
        if hero_features['has_live_video_tour']:
            markdown_parts.append(f"- ✅ Live Video Tour Available\n")
        if hero_features['has_map']:
            markdown_parts.append(f"- ✅ Map View Available\n")
        if hero_features['has_street_view']:
            markdown_parts.append(f"- ✅ Street View Available\n")
        if hero_features['has_price_display']:
            markdown_parts.append(f"- ✅ Price Display in Hero\n")
        if hero_features['on_site_video']:
            markdown_parts.append(f"- ✅ On-Site Video Available\n")
        markdown_parts.append(f"\n**Media Counts:**\n")
        markdown_parts.append(f"- Video Count: {hero_features['video_count']}\n")
        
        # Videos
        videos = self.extract_videos(data)
        if videos:
            markdown_parts.append(f"\n**Videos:**\n")
            for video in videos:
                video_type = video.get('type', 'video').replace('_', ' ').title()
                markdown_parts.append(f"- **{video_type}**: {video.get('caption', 'Property Video')} - {video.get('url', '')}\n")
        
        # Virtual Tours (360°/VR)
        virtual_tours = self.extract_virtual_tours(data)
        if virtual_tours:
            markdown_parts.append(f"\n**Virtual Tours (360°):**\n")
            for tour in virtual_tours:
                markdown_parts.append(f"- **{tour.get('room_type', 'Property')}**: {tour.get('url', '')}\n")
        
        # About Property
        about = data.get('about', {}) if isinstance(data.get('about'), dict) else {}
        if isinstance(about, dict) and about.get('text_strip_html'):
            markdown_parts.append(f"\n## About Property\n\n{about['text_strip_html']}\n")
        
        # Demographics/Overview
        if about.get('overview'):
            markdown_parts.append(f"\n## Demographics\n\n")
            for item in about['overview']:
                title = item.get('title', '')
                answer = item.get('answer', '')
                markdown_parts.append(f"- **{title}**: {answer}\n")
        
        # Pricing
        house = data.get('house', {}) if isinstance(data.get('house'), dict) else {}
        if isinstance(house, dict) and house.get('rent_amount'):
            rent = house['rent_amount']
            currency = rent.get('abbr', '£')
            amount = rent.get('amount', 'N/A')
            lease_unit = house.get('lease_unit', 'week')
            
            markdown_parts.append(f"\n## Pricing\n\n")
            markdown_parts.append(f"Price: {currency}{amount} / {lease_unit}\n")
        
        # Payment Details (Enhanced)
        payment_details = self.extract_payment_details(data)
        if payment_details['installment_options'] or payment_details['payment_methods']:
            markdown_parts.append(f"\n## Payment Details\n\n")
            if payment_details['installment_options']:
                options = ', '.join(map(str, payment_details['installment_options']))
                markdown_parts.append(f"**Installment Options:** {options} instalments available\n")
            if payment_details['payment_method_ids']:
                markdown_parts.append(f"**Payment Methods:** Available (Method IDs: {payment_details['payment_method_ids']})\n")
            if payment_details['guarantor_required']:
                markdown_parts.append(f"**Guarantor:** Required\n")
            if payment_details['deposit']:
                dep = payment_details['deposit']
                markdown_parts.append(f"**Deposit:** {dep.get('currency', '£')}{dep.get('amount', '')} ({dep.get('payment_time', '')})\n")
            if payment_details['other_fees']:
                markdown_parts.append(f"\n**Other Fees:**\n")
                for fee in payment_details['other_fees']:
                    markdown_parts.append(f"- **{fee.get('title', 'Fee')}**: {fee.get('currency', '£')}{fee.get('amount', '')} ({fee.get('payment_time', '')})\n")
        
        # Deposit (legacy format for compatibility)
        fees = data.get('fees', {}) if isinstance(data.get('fees'), dict) else {}
        if isinstance(fees, dict) and fees.get('deposit'):
            deposit = fees['deposit'].get('amount', {})
            deposit_currency = deposit.get('abbr', '£') if isinstance(deposit, dict) else '£'
            deposit_amount = deposit.get('amount', 'N/A') if isinstance(deposit, dict) else deposit
            markdown_parts.append(f"\nDeposit: {deposit_currency}{deposit_amount}\n")
        
        # Built Year
        if house.get('built_date'):
            markdown_parts.append(f"Built Year: {house['built_date']}\n")
        
        # Unit Count
        if house.get('unit_count'):
            markdown_parts.append(f"Total Units: {house['unit_count']}\n")
        
        # Room Types (Enhanced - from room_type_items)
        room_types = self.extract_room_types(data)
        if room_types:
            markdown_parts.append(f"\n## Room Types\n\n")
            for room in room_types:
                room_name = room.get('name', 'Unknown')
                room_price = room.get('price', 'N/A')
                currency = room.get('currency', '£')
                area_sqm = room.get('area_sqm', {})
                area_max = area_sqm.get('max', '') if isinstance(area_sqm, dict) else ''
                
                markdown_parts.append(f"- **{room_name}**: {currency}{room_price}")
                if area_max:
                    markdown_parts[-1] += f" ({area_max} sqm)"
                if room.get('has_360_tour'):
                    markdown_parts[-1] += " [360° Tour Available]"
                markdown_parts[-1] += "\n"
        
        # Features/Amenities
        features = data.get('features', [])
        if features:
            markdown_parts.append(f"\n## Amenities\n\n")
            for feature in features:
                feature_name = feature.get('name', '')
                if feature_name:
                    markdown_parts.append(f"- {feature_name}\n")
        
        # Offers (Enhanced)
        offers = self.extract_offers_details(data)
        if offers:
            markdown_parts.append(f"\n## Offers\n\n")
            for offer in offers:
                offer_name = offer.get('name', 'Offer')
                offer_desc = offer.get('description', '')
                offer_type = offer.get('type', '')
                if offer.get('amount'):
                    markdown_parts.append(f"- **{offer_name}** ({offer_type}): {offer_desc}\n")
                else:
                    markdown_parts.append(f"- **{offer_name}** ({offer_type}): {offer_desc}\n")
        
        # FAQs - check multiple possible locations
        faqs = []
        # Check 'faq' key first
        if data.get('faq'):
            faqs = data.get('faq', [])
        # Check 'features_faq' if 'faq' is empty
        elif data.get('features_faq'):
            faqs = data.get('features_faq', [])
        
        if faqs and len(faqs) > 0:
            markdown_parts.append(f"\n## FAQs\n\n")
            for faq in faqs:
                question = faq.get('question') or faq.get('title', '') or faq.get('q', '')
                answer = faq.get('answer') or faq.get('content', '') or faq.get('a', '')
                if question and answer:
                    markdown_parts.append(f"### Q: {question}\n\nA: {answer}\n\n")
        
        # Cancellation Policies
        rules = data.get('rules', [])
        if rules:
            cancel_rules = [r for r in rules if r.get('policy_type') == 'cancel']
            if cancel_rules:
                markdown_parts.append(f"\n## Cancellation Policy\n\n")
                for rule in cancel_rules:
                    policy_text = rule.get('policy_text', {}).get('text', '')
                    if policy_text:
                        markdown_parts.append(f"{policy_text}\n")
        
        # Nearby Locations
        nearby = data.get('nearby', [])
        if nearby:
            markdown_parts.append(f"\n## Nearby Locations\n\n")
            for location in nearby:
                name = location.get('name') or location.get('title', '')
                distance = location.get('distance', 'N/A')
                markdown_parts.append(f"- **{name}**: {distance}\n")
        
        # Nearby Properties
        nearby_properties = self.extract_nearby_properties(data)
        if nearby_properties:
            markdown_parts.append(f"\n## Nearby Properties\n\n")
            for prop in nearby_properties:
                markdown_parts.append(f"- **{prop.get('name', '')}**: {prop.get('distance', '')} - {prop.get('url', '')}\n")
        
        # Images (Enhanced - from media array)
        all_media = self.extract_all_media(data)
        if all_media['images']:
            markdown_parts.append(f"\n## Images\n\n")
            markdown_parts.append(f"Total Images: {all_media['total_images']}\n")
            for img in all_media['images'][:10]:  # First 10 images
                img_url = img.get('url', '')
                img_type = img.get('type', '')
                if img_url:
                    markdown_parts.append(f"- ![]({img_url}) - {img_type}\n")
        
        # Also include images from media.images for backward compatibility
        media = data.get('media', {}) if isinstance(data.get('media'), dict) else {}
        images = media.get('images', []) if isinstance(media, dict) else []
        if images and not all_media['images']:
            markdown_parts.append(f"\n## Images\n\n")
            markdown_parts.append(f"Total Images: {len(images)}\n")
            for img in images[:10]:  # First 10 images
                img_url = img.get('url', '') or img.get('src', '') or img.get('path', '')
                img_type = img.get('type', '')
                img_caption = img.get('caption', '')
                if img_url:
                    if img_caption:
                        markdown_parts.append(f"- ![{img_caption}]({img_url}) - {img_type}\n")
                    else:
                        markdown_parts.append(f"- ![]({img_url}) - {img_type}\n")
        
        # Links (extract from about text HTML)
        about = data.get('about', {})
        all_links = []
        if isinstance(about, dict):
            about_text = about.get('text', '')
            if about_text:
                all_links = self.extract_links_from_html(about_text)
        
        if all_links:
            markdown_parts.append(f"\n## Links\n\n")
            unique_links = list(set(all_links))
            for link in unique_links[:20]:  # First 20 unique links
                markdown_parts.append(f"- {link}\n")
        
        return '\n'.join(markdown_parts)
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape UHomes property using browser automation
        
        Args:
            url: UHomes property URL
            
        Returns:
            Dict with scraped data (compatible with Firecrawl format)
        """
        try:
            # Extract __NUXT__ data
            if self.use_playwright:
                h_data = self.extract_nuxt_data_playwright(url)
            else:
                h_data = self.extract_nuxt_data_selenium(url)
            
            # Ensure h_data is a dict
            if not isinstance(h_data, dict):
                self.logger.error(f"h_data is not a dict, got {type(h_data)}")
                raise Exception(f"Invalid h_data format: expected dict, got {type(h_data)}")
            
            # Convert to markdown
            markdown = self.json_to_markdown(h_data, 'uhomes')
            
            # Extract metadata
            house = h_data.get('house', {}) if isinstance(h_data.get('house'), dict) else {}
            property_name = house.get('title', 'Unknown Property') if isinstance(house, dict) else 'Unknown Property'
            
            # Extract all media from media array
            all_media = self.extract_all_media(h_data)
            image_urls = [img.get('url', '') for img in all_media['images'] if img.get('url')]
            
            # Also check media.images for backward compatibility
            media = h_data.get('media', {}) if isinstance(h_data.get('media'), dict) else {}
            images = media.get('images', []) if isinstance(media, dict) and isinstance(media.get('images'), list) else []
            for img in images:
                if isinstance(img, dict):
                    url = img.get('url') or img.get('src') or img.get('path', '')
                    if url and url not in image_urls:
                        image_urls.append(url)
            
            # Extract links from about text HTML
            links = []
            about = h_data.get('about', {})
            if isinstance(about, dict):
                about_text = about.get('text', '')
                if about_text:
                    links = self.extract_links_from_html(about_text)
            
            # Extract videos
            videos = self.extract_videos(h_data)
            video_urls = [v.get('url', '') for v in videos if v.get('url')]
            
            # Extract virtual tours
            virtual_tours = self.extract_virtual_tours(h_data)
            virtual_tour_urls = [vt.get('url', '') for vt in virtual_tours if vt.get('url')]
            
            # Extract room types
            room_types = self.extract_room_types(h_data)
            
            # Extract hero features
            hero_features = self.extract_hero_features(h_data)
            
            # Extract payment details
            payment_details = self.extract_payment_details(h_data)
            
            # Extract offers
            offers = self.extract_offers_details(h_data)
            
            # Extract nearby properties
            nearby_properties = self.extract_nearby_properties(h_data)
            
            # Remove duplicate links
            unique_links = list(set(links))
            
            self.logger.info(
                f"✅ Scraped successfully: {len(markdown)} chars markdown, "
                f"{len(image_urls)} images, {len(video_urls)} videos, "
                f"{len(virtual_tour_urls)} virtual tours, {len(room_types)} room types, "
                f"{len(unique_links)} links"
            )
            
            return {
                'success': True,
                'url': url,
                'markdown': markdown,
                'html': '',  # Not extracted
                'metadata': {
                    'title': property_name,
                    'description': h_data.get('about', {}).get('text_strip_html', ''),
                    'images': image_urls,
                    'links': unique_links,
                    'videos': video_urls,
                    'virtual_tours': virtual_tour_urls,
                    'room_types': room_types,
                    'hero_features': hero_features,
                    'payment_details': payment_details,
                    'offers': offers,
                    'nearby_properties': nearby_properties,
                    'source_url': url
                },
                'scraper': 'uhomes_puppeteer',
                'raw_json': h_data  # Store raw JSON for detailed comparison
            }
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__,
                'scraper': 'uhomes_puppeteer'
            }


if __name__ == "__main__":
    # Test scraper
    try:
        scraper = UHomesPuppeteerScraper(use_playwright=False)  # Use Selenium
        
        test_url = "https://en.uhomes.com/uk/aberdeen/detail-apartments-530876"
        result = scraper.scrape_url(test_url)
        
        if result['success']:
            print(f"✅ Success! Property: {result['metadata']['title']}")
            print(f"Markdown length: {len(result['markdown'])} chars")
            print(f"Images: {len(result['metadata']['images'])}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Install Selenium: pip install selenium")
        print("Or install Playwright: pip install playwright && playwright install")

