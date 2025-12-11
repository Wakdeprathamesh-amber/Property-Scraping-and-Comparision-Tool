"""
Bulk Scraper
Scrapes properties using Firecrawl and stores in Google Sheets
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, Tuple, List
import pandas as pd
from dotenv import load_dotenv

from src.sheets_manager import SheetsManager
from src.scrapers.scraper_factory import ScraperFactory
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()


class BulkScraper:
    """Bulk scrape properties from Google Sheets"""
    
    def __init__(self, prefer_api: bool = True, use_playwright: bool = False, 
                 delay_min: int = 5, delay_max: int = 10):
        """
        Initialize bulk scraper
        
        Args:
            prefer_api: Prefer API scrapers over Firecrawl (default: True)
            use_playwright: Use Playwright for UHomes instead of Selenium (default: False)
            delay_min: Minimum delay between requests in seconds (default: 5)
            delay_max: Maximum delay between requests in seconds (default: 10)
        """
        self.logger = setup_logger(self.__class__.__name__)
        self.sheets = SheetsManager()
        
        # Initialize scraper factory (uses API scrapers by default, Firecrawl as fallback)
        self.scraper_factory = ScraperFactory(prefer_api=prefer_api, use_playwright=use_playwright)
        
        # Rate limiting delays
        self.delay_min = delay_min
        self.delay_max = delay_max
        
        # Create backup directory for full markdown files
        from pathlib import Path
        self.backup_dir = Path('scraped_data_backup')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Create directory for raw JSON backups
        self.json_backup_dir = Path('scraped_json_backup')
        self.json_backup_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"✅ Bulk scraper initialized (API scrapers preferred, delays: {delay_min}-{delay_max}s)")
    
    def _save_full_markdown(self, property_id: str, platform: str, markdown: str):
        """Save full markdown to local file as backup"""
        try:
            filename = self.backup_dir / f"{property_id}_{platform}_full.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown)
            self.logger.info(f"  💾 Saved full markdown to {filename}")
        except Exception as e:
            self.logger.warning(f"Could not save backup markdown: {e}")
    
    def _save_raw_json(self, property_id: str, platform: str, raw_json: Dict[str, Any]):
        """Save raw JSON data to local file as backup"""
        try:
            filename = self.json_backup_dir / f"{property_id}_{platform}_raw.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(raw_json, f, indent=2, ensure_ascii=False)
            self.logger.info(f"  💾 Saved raw JSON to {filename}")
        except Exception as e:
            self.logger.warning(f"Could not save backup JSON: {e}")
    
    def _wait_between_requests(self):
        """Wait random delay between requests to avoid rate limiting"""
        delay = random.uniform(self.delay_min, self.delay_max)
        self.logger.info(f"  ⏳ Waiting {delay:.1f} seconds to avoid rate limiting...")
        time.sleep(delay)
    
    def scrape_url(self, url: str, property_id: str, platform: str) -> Tuple[bool, List[Any]]:
        """
        Scrape a single URL using appropriate scraper (API or Firecrawl)
        
        Args:
            url: URL to scrape
            property_id: Property ID (e.g., 'P001')
            platform: 'amber' or 'uhomes'
            
        Returns:
            Tuple of (success, scraped_data)
        """
        self.logger.info(f"🔥 Scraping {platform} URL for {property_id}: {url}")
        
        try:
            # Use scraper factory to get appropriate scraper
            result = self.scraper_factory.scrape_url(url, platform=platform)
            
            # Log which scraper was used
            scraper_used = result.get('scraper_used', 'unknown')
            self.logger.info(f"  Using scraper: {scraper_used}")
            
            if not result.get('success', False) or 'markdown' not in result:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"❌ Scraping failed for {url}: {error_msg}")
                return False, {}
            
            # Extract data
            markdown = result.get('markdown', '')
            metadata = result.get('metadata', {})
            raw_json = result.get('raw_json', {})  # Get raw JSON if available
            images = metadata.get('images', []) if metadata else []
            links = metadata.get('links', []) if metadata else []
            videos = metadata.get('videos', []) if metadata else []
            virtual_tours = metadata.get('virtual_tours', []) if metadata else []
            
            # Extract property name from metadata or markdown
            property_name = metadata.get('title', 'Unknown Property')
            
            # Try to extract city from URL or metadata
            city = 'Unknown'
            if 'london' in url.lower():
                city = 'London'
            elif 'aberdeen' in url.lower():
                city = 'Aberdeen'
            elif 'birmingham' in url.lower():
                city = 'Birmingham'
            elif metadata.get('location'):
                city = metadata.get('location')
            elif metadata.get('location_details', {}).get('city'):
                city = metadata.get('location_details', {}).get('city')
            
            # Count items
            images_count = len(images) if isinstance(images, list) else 0
            videos_count = len(videos) if isinstance(videos, list) else 0
            virtual_tours_count = len(virtual_tours) if isinstance(virtual_tours, list) else 0
            links_count = len(links) if isinstance(links, list) else 0
            word_count = len(markdown.split()) if markdown else 0
            
            # Prepare data for sheet (truncate markdown to fit Google Sheets 50k limit)
            markdown_truncated = markdown[:45000] if len(markdown) > 45000 else markdown
            
            # Prepare raw JSON for storage (truncate if too large)
            raw_json_str = ''
            if raw_json:
                try:
                    raw_json_str = json.dumps(raw_json, ensure_ascii=False)
                    # Truncate to 45k chars for Google Sheets limit (but keep valid JSON)
                    if len(raw_json_str) > 45000:
                        # Try to truncate at a safe point (end of a key-value pair)
                        truncated = raw_json_str[:44700]  # Leave room for closing brace
                        # Find last complete key-value pair
                        last_comma = truncated.rfind(',')
                        if last_comma > 44000:  # If we found a comma near the end
                            truncated = truncated[:last_comma]
                        raw_json_str = truncated + '..."truncated":true}'
                        self.logger.warning(f"  ⚠️ JSON truncated to fit Google Sheets (original: {len(json.dumps(raw_json, ensure_ascii=False)):,} chars)")
                except Exception as e:
                    self.logger.warning(f"  ⚠️ Could not serialize JSON: {e}")
                    raw_json_str = json.dumps({'error': 'Could not serialize', 'type': str(type(raw_json))}, ensure_ascii=False)
            
            # Extract structured data separately (to avoid truncation in Metadata_JSON)
            # Basic metadata (title, description, images, links) - keep small
            basic_metadata = {
                'title': metadata.get('title', ''),
                'description': metadata.get('description', '')[:1000],  # Truncate description
                'images': images[:10],  # First 10 images only
                'links': links[:20]  # First 20 links only
            }
            
            # Extract structured data separately
            hero_features = metadata.get('hero_features', {})
            payment_details = metadata.get('payment_details', {})
            offers = metadata.get('offers', [])
            nearby_properties = metadata.get('nearby_properties', [])
            room_types = metadata.get('room_types', [])  # For UHomes
            property_metadata = metadata.get('property_metadata', {})  # For Amber
            
            # Serialize structured data (no truncation - stored in separate columns)
            hero_features_json = json.dumps(hero_features, ensure_ascii=False) if hero_features else ''
            payment_details_json = json.dumps(payment_details, ensure_ascii=False) if payment_details else ''
            offers_json = json.dumps(offers, ensure_ascii=False) if offers else ''
            nearby_properties_json = json.dumps(nearby_properties, ensure_ascii=False) if nearby_properties else ''
            room_types_json = json.dumps(room_types, ensure_ascii=False) if room_types else ''
            property_metadata_json = json.dumps(property_metadata, ensure_ascii=False) if property_metadata else ''
            videos_json = json.dumps(videos, ensure_ascii=False) if videos else ''
            virtual_tours_json = json.dumps(virtual_tours, ensure_ascii=False) if virtual_tours else ''
            
            # Create data in exact order matching sheet headers
            scraped_data = [
                property_id,                    # Property_ID
                platform,                       # Platform
                property_name,                  # Property_Name
                city,                           # City
                'UK',                           # Country
                markdown_truncated,             # Markdown_Content
                raw_json_str,                   # Raw_JSON_Data
                json.dumps(basic_metadata, ensure_ascii=False),  # Metadata_JSON (basic only)
                hero_features_json,             # Hero_Features_JSON
                payment_details_json,           # Payment_Details_JSON
                offers_json,                    # Offers_JSON
                nearby_properties_json,         # Nearby_Properties_JSON
                room_types_json,                # Room_Types_JSON
                property_metadata_json,         # Property_Metadata_JSON
                videos_json,                    # Videos_JSON
                virtual_tours_json,             # Virtual_Tours_JSON
                images_count,                   # Images_Count
                ', '.join(images[:10]) if images else '',  # Images_URLs
                videos_count,                  # Videos_Count
                virtual_tours_count,           # Virtual_Tours_Count
                links_count,                    # Links_Count
                word_count,                     # Word_Count
                result.get('scraper_used', 'unknown'),  # Scraper_Used
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Scraped_At
            ]
            
            # Also save full markdown and JSON to local files for backup
            self._save_full_markdown(property_id, platform, markdown)
            if raw_json:
                self._save_raw_json(property_id, platform, raw_json)
            
            self.logger.info(f"✅ Scraped {platform}: {property_name} ({word_count} words, {images_count} images)")
            
            return True, scraped_data
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping {url}: {e}")
            return False, {}
    
    def process_property(self, property_row: pd.Series) -> bool:
        """
        Process a single property (scrape both Amber and Uhomes)
        
        Args:
            property_row: Row from Input_Properties sheet
            
        Returns:
            Success status
        """
        property_id = property_row['Property_ID']
        amber_url = property_row['Amber_URL']
        uhomes_url = property_row['Uhomes_URL']
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"Processing Property: {property_id}")
        self.logger.info(f"{'='*80}")
        
        # Update status to 'processing'
        try:
            self.sheets.find_and_update(
                'Input_Properties',
                search_col='Property_ID',
                search_value=property_id,
                update_col='Status',
                update_value='processing'
            )
        except Exception as e:
            self.logger.warning(f"Could not update status: {e}")
        
        success_count = 0
        
        # Scrape Amber URL
        self.logger.info(f"  📍 Scraping Amber: {amber_url}")
        success_amber, amber_data = self.scrape_url(amber_url, property_id, 'amber')
        if success_amber:
            # Write to Raw_Scraped_Data sheet
            try:
                self.sheets.append_row('Raw_Scraped_Data', amber_data)  # Already a list
                success_count += 1
                self.logger.info(f"  ✅ Amber data saved to sheet")
            except Exception as e:
                self.logger.error(f"Error writing Amber data to sheet: {e}")
        else:
            self.logger.error(f"  ❌ Amber scraping failed")
        
        # Wait between requests to avoid rate limiting
        self._wait_between_requests()
        
        # Scrape Uhomes URL
        self.logger.info(f"  📍 Scraping UHomes: {uhomes_url}")
        success_uhomes, uhomes_data = self.scrape_url(uhomes_url, property_id, 'uhomes')
        if success_uhomes:
            # Write to Raw_Scraped_Data sheet
            try:
                self.sheets.append_row('Raw_Scraped_Data', uhomes_data)  # Already a list
                success_count += 1
                self.logger.info(f"  ✅ UHomes data saved to sheet")
            except Exception as e:
                self.logger.error(f"Error writing Uhomes data to sheet: {e}")
        else:
            self.logger.error(f"  ❌ UHomes scraping failed")
        
        # Update final status
        if success_count == 2:
            final_status = 'scraped'
            self.logger.info(f"✅ {property_id} fully scraped (both platforms)")
        elif success_count == 1:
            final_status = 'partial'
            self.logger.warning(f"⚠️ {property_id} partially scraped (1 of 2 platforms)")
        else:
            final_status = 'failed'
            self.logger.error(f"❌ {property_id} scraping failed")
        
        try:
            self.sheets.find_and_update(
                'Input_Properties',
                search_col='Property_ID',
                search_value=property_id,
                update_col='Status',
                update_value=final_status
            )
        except Exception as e:
            self.logger.warning(f"Could not update final status: {e}")
        
        return success_count == 2
    
    def process_all_pending(self) -> Dict[str, int]:
        """
        Process all properties with 'pending' status
        
        Returns:
            Dictionary with statistics
        """
        self.logger.info("\n" + "="*80)
        self.logger.info("BULK SCRAPING - Starting")
        self.logger.info("="*80)
        
        # Get pending properties
        try:
            df = self.sheets.read_sheet('Input_Properties')
            pending_df = df[df['Status'] == 'pending']
            
            if len(pending_df) == 0:
                self.logger.info("No pending properties found")
                return {'total': 0, 'success': 0, 'failed': 0}
            
            self.logger.info(f"Found {len(pending_df)} pending properties")
            
        except Exception as e:
            self.logger.error(f"Error reading properties: {e}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        # Process each property
        stats = {'total': len(pending_df), 'success': 0, 'failed': 0}
        
        for idx, row in pending_df.iterrows():
            success = self.process_property(row)
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # Wait between properties to avoid rate limiting
            # (except after the last property)
            if idx < len(pending_df) - 1:
                self._wait_between_requests()
        
        # Summary
        self.logger.info("\n" + "="*80)
        self.logger.info("BULK SCRAPING - Complete")
        self.logger.info("="*80)
        self.logger.info(f"Total properties: {stats['total']}")
        self.logger.info(f"✅ Successfully scraped: {stats['success']}")
        self.logger.info(f"❌ Failed: {stats['failed']}")
        self.logger.info("="*80)
        
        return stats


def main():
    """Main execution"""
    try:
        scraper = BulkScraper()
        stats = scraper.process_all_pending()
        
        print("\n" + "="*80)
        print("SCRAPING RESULTS")
        print("="*80)
        print(f"Total: {stats['total']}")
        print(f"✅ Success: {stats['success']}")
        print(f"❌ Failed: {stats['failed']}")
        print("="*80)
        print("\nCheck your Google Sheets:")
        print("1. Input_Properties - Status updated to 'scraped'")
        print("2. Raw_Scraped_Data - New rows with scraped content")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

