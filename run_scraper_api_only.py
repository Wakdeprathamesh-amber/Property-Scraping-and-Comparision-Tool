"""
Run scraping using ONLY API scrapers (no Firecrawl fallback)
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, Tuple, List
import pandas as pd
from pathlib import Path

from src.sheets_manager import SheetsManager
from src.scrapers.amber_api_scraper import AmberAPIScraper
from src.scrapers.uhomes_puppeteer_scraper import UHomesPuppeteerScraper
from src.utils.logger import setup_logger

logger = setup_logger("APIBulkScraper")


def scrape_url_api_only(url: str, property_id: str, platform: str, sheets: SheetsManager) -> Tuple[bool, List[Any]]:
    """
    Scrape URL using ONLY API scrapers (no Firecrawl fallback)
    """
    logger.info(f"🔥 Scraping {platform} URL for {property_id}: {url} (API ONLY)")
    
    try:
        # Use API scrapers directly (no factory, no fallback)
        if platform == 'amber':
            scraper = AmberAPIScraper()
            result = scraper.scrape_url(url)
            scraper_used = 'amber_api'
        elif platform == 'uhomes':
            scraper = UHomesPuppeteerScraper(use_playwright=False)
            result = scraper.scrape_url(url)
            scraper_used = 'uhomes_puppeteer'
        else:
            raise ValueError(f"Unknown platform: {platform}")
        
        if not result.get('success', False) or 'markdown' not in result:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ API scraping failed for {url}: {error_msg}")
            logger.error(f"   ⚠️  No Firecrawl fallback - failing")
            return False, {}
        
        # Extract data
        markdown = result.get('markdown', '')
        metadata = result.get('metadata', {})
        raw_json = result.get('raw_json', {})
        images = metadata.get('images', []) if metadata else []
        links = metadata.get('links', []) if metadata else []
        videos = metadata.get('videos', []) if metadata else []
        virtual_tours = metadata.get('virtual_tours', []) if metadata else []
        
        # Extract property name
        property_name = metadata.get('title', 'Unknown Property')
        
        # Extract city
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
        
        # Prepare markdown (truncate if needed)
        markdown_truncated = markdown[:45000] if len(markdown) > 45000 else markdown
        
        # Prepare raw JSON
        raw_json_str = ''
        if raw_json:
            try:
                raw_json_str = json.dumps(raw_json, ensure_ascii=False)
                if len(raw_json_str) > 45000:
                    truncated = raw_json_str[:44700]
                    last_comma = truncated.rfind(',')
                    if last_comma > 44000:
                        truncated = truncated[:last_comma]
                    raw_json_str = truncated + '..."truncated":true}'
                    logger.warning(f"  ⚠️ JSON truncated to fit Google Sheets")
            except Exception as e:
                logger.warning(f"  ⚠️ Could not serialize JSON: {e}")
                raw_json_str = json.dumps({'error': 'Could not serialize', 'type': str(type(raw_json))}, ensure_ascii=False)
        
        # Basic metadata
        basic_metadata = {
            'title': metadata.get('title', ''),
            'description': metadata.get('description', '')[:1000],
            'images': images[:10],
            'links': links[:20]
        }
        
        # Extract structured data
        hero_features = metadata.get('hero_features', {})
        payment_details = metadata.get('payment_details', {})
        offers = metadata.get('offers', [])
        nearby_properties = metadata.get('nearby_properties', [])
        room_types = metadata.get('room_types', [])
        property_metadata = metadata.get('property_metadata', {})
        
        # Serialize structured data
        hero_features_json = json.dumps(hero_features, ensure_ascii=False) if hero_features else ''
        payment_details_json = json.dumps(payment_details, ensure_ascii=False) if payment_details else ''
        offers_json = json.dumps(offers, ensure_ascii=False) if offers else ''
        nearby_properties_json = json.dumps(nearby_properties, ensure_ascii=False) if nearby_properties else ''
        room_types_json = json.dumps(room_types, ensure_ascii=False) if room_types else ''
        property_metadata_json = json.dumps(property_metadata, ensure_ascii=False) if property_metadata else ''
        videos_json = json.dumps(videos, ensure_ascii=False) if videos else ''
        virtual_tours_json = json.dumps(virtual_tours, ensure_ascii=False) if virtual_tours else ''
        
        # Create data row
        scraped_data = [
            property_id,
            platform,
            property_name,
            city,
            'UK',
            markdown_truncated,
            raw_json_str,
            json.dumps(basic_metadata, ensure_ascii=False),
            hero_features_json,
            payment_details_json,
            offers_json,
            nearby_properties_json,
            room_types_json,
            property_metadata_json,
            videos_json,
            virtual_tours_json,
            images_count,
            ', '.join(images[:10]) if images else '',
            videos_count,
            virtual_tours_count,
            links_count,
            word_count,
            scraper_used,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Save backups
        backup_dir = Path('scraped_data_backup')
        backup_dir.mkdir(exist_ok=True)
        json_backup_dir = Path('scraped_json_backup')
        json_backup_dir.mkdir(exist_ok=True)
        
        filename = backup_dir / f"{property_id}_{platform}_full.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        if raw_json:
            json_filename = json_backup_dir / f"{property_id}_{platform}_raw.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(raw_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Scraped {platform}: {property_name} ({word_count} words, {images_count} images)")
        
        return True, scraped_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping {url}: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def main():
    print("\n" + "="*80)
    print("🔥 BULK PROPERTY SCRAPER (API ONLY)")
    print("="*80)
    print("\nThis will:")
    print("1. Find all 'pending' properties in Google Sheets")
    print("2. Scrape using ONLY API scrapers (Amber API, UHomes Puppeteer)")
    print("3. NO Firecrawl fallback - will fail if API scrapers fail")
    print("4. Save raw data to 'Raw_Scraped_Data' sheet")
    print("5. Update status to 'scraped'")
    print("\n" + "="*80)
    
    try:
        sheets = SheetsManager()
        
        # Get pending properties
        df = sheets.read_sheet('Input_Properties')
        pending_df = df[df['Status'] == 'pending']
        
        if len(pending_df) == 0:
            print("No pending properties found")
            return
        
        print(f"\nFound {len(pending_df)} pending properties")
        
        stats = {'total': len(pending_df), 'success': 0, 'failed': 0}
        
        for idx, row in pending_df.iterrows():
            property_id = row['Property_ID']
            amber_url = row['Amber_URL']
            uhomes_url = row['Uhomes_URL']
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing Property: {property_id}")
            logger.info(f"{'='*80}")
            
            # Update status to processing
            try:
                sheets.find_and_update(
                    'Input_Properties',
                    search_col='Property_ID',
                    search_value=property_id,
                    update_col='Status',
                    update_value='processing'
                )
            except Exception as e:
                logger.warning(f"Could not update status: {e}")
            
            success_count = 0
            
            # Scrape Amber
            logger.info(f"  📍 Scraping Amber: {amber_url}")
            success_amber, amber_data = scrape_url_api_only(amber_url, property_id, 'amber', sheets)
            if success_amber:
                try:
                    sheets.append_row('Raw_Scraped_Data', amber_data)
                    success_count += 1
                    logger.info(f"  ✅ Amber data saved to sheet")
                except Exception as e:
                    logger.error(f"Error writing Amber data to sheet: {e}")
            else:
                logger.error(f"  ❌ Amber scraping failed")
            
            # Wait between requests
            delay = random.uniform(5, 10)
            logger.info(f"  ⏳ Waiting {delay:.1f} seconds...")
            time.sleep(delay)
            
            # Scrape UHomes
            logger.info(f"  📍 Scraping UHomes: {uhomes_url}")
            success_uhomes, uhomes_data = scrape_url_api_only(uhomes_url, property_id, 'uhomes', sheets)
            if success_uhomes:
                try:
                    sheets.append_row('Raw_Scraped_Data', uhomes_data)
                    success_count += 1
                    logger.info(f"  ✅ UHomes data saved to sheet")
                except Exception as e:
                    logger.error(f"Error writing UHomes data to sheet: {e}")
            else:
                logger.error(f"  ❌ UHomes scraping failed")
            
            # Update final status
            if success_count == 2:
                final_status = 'scraped'
                logger.info(f"✅ {property_id} fully scraped (both platforms)")
            elif success_count == 1:
                final_status = 'partial'
                logger.warning(f"⚠️ {property_id} partially scraped (1 of 2 platforms)")
            else:
                final_status = 'failed'
                logger.error(f"❌ {property_id} scraping failed")
            
            try:
                sheets.find_and_update(
                    'Input_Properties',
                    search_col='Property_ID',
                    search_value=property_id,
                    update_col='Status',
                    update_value=final_status
                )
            except Exception as e:
                logger.warning(f"Could not update final status: {e}")
            
            if success_count == 2:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # Wait between properties
            if idx < len(pending_df) - 1:
                delay = random.uniform(5, 10)
                logger.info(f"  ⏳ Waiting {delay:.1f} seconds before next property...")
                time.sleep(delay)
        
        # Summary
        print("\n" + "="*80)
        print("✅ SCRAPING COMPLETE (API ONLY)!")
        print("="*80)
        print(f"Processed: {stats['total']} properties")
        print(f"Success: {stats['success']} properties")
        print(f"Failed: {stats['failed']} properties")
        print("="*80)
        print("\n📊 Check your Google Sheets:")
        print("   - Input_Properties (status updated)")
        print("   - Raw_Scraped_Data (new scraped content)")
        print("\n⚠️  Note: Only API scrapers were used (no Firecrawl)")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

