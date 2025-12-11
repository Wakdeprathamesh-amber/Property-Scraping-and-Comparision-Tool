# Scraping Guide

This document explains how the scraping process works for both Amber and UHomes platforms.

---

## Overview

The scraping module fetches property data from two sources:
- **Amber**: Direct API calls (most reliable)
- **UHomes**: Browser automation extracting `window.__NUXT__` data

---

## Entry Point

**File:** `run_scraper_api_only.py`

**Usage:**
```bash
python3 run_scraper_api_only.py
```

---

## How It Works

### Step 1: Read Input Properties

Reads from `Input_Properties` Google Sheet:
- Filters for `Status == 'pending'`
- Extracts `Property_ID`, `Amber_URL`, `Uhomes_URL`

### Step 2: Scrape Each Platform

For each property:
1. **Scrape Amber** using `AmberAPIScraper`
2. **Wait** 5-10 seconds (rate limiting)
3. **Scrape UHomes** using `UHomesPuppeteerScraper`
4. **Wait** 5-10 seconds before next property

### Step 3: Store Results

- Writes to `Raw_Scraped_Data` Google Sheet
- Creates backup files:
  - `scraped_json_backup/{Property_ID}_{platform}_raw.json`
  - `scraped_data_backup/{Property_ID}_{platform}_full.md`

### Step 4: Update Status

Updates `Input_Properties` sheet:
- `Status = 'scraped'` (both platforms successful)
- `Status = 'partial'` (one platform successful)
- `Status = 'failed'` (both platforms failed)

---

## Amber Scraper

**File:** `src/scrapers/amber_api_scraper.py`

### How It Works

1. **Extract Canonical Name** from URL
   - URL: `https://amberstudent.com/places/ben-russell-court-leicester-1608300341147`
   - Canonical: `ben-russell-court-leicester-1608300341147`

2. **Fetch Property Data**
   - API: `https://base.amberstudent.com/api/v0/inventories/{canonical_name}`
   - Returns: Complete property JSON

3. **Fetch Room Types** (optional, for detailed room data)
   - API: `https://base.amberstudent.com/api/v0/inventories/{canonical_name}/room_types`
   - Paginated: Handles multiple pages automatically

4. **Extract Structured Data**
   - Hero features (360° tours, videos, map)
   - Payment details (installments, methods, guarantor)
   - Offers (cashback, promotions)
   - Room types, amenities, FAQs, etc.

5. **Convert to Markdown**
   - Converts JSON to markdown format
   - Compatible with existing analysis pipeline

### Data Structure

```python
{
    'success': True,
    'url': 'https://amberstudent.com/places/...',
    'markdown': '# Property Name\n\n...',
    'metadata': {
        'title': 'Property Name',
        'images': [...],
        'videos': [...],
        'virtual_tours': [...],
        'hero_features': {...},
        'payment_details': {...},
        'offers': [...],
        'room_types': [...],
        'nearby_properties': [...]
    },
    'raw_json': {...}  # Full API response
}
```

---

## UHomes Scraper

**File:** `src/scrapers/uhomes_puppeteer_scraper.py`

### How It Works

1. **Launch Browser** (Selenium or Playwright)
   - Headless Chrome
   - Custom user agent
   - Timeout: 90 seconds

2. **Navigate to URL**
   - Loads the property page
   - Waits for JavaScript to execute

3. **Extract `window.__NUXT__` Data**
   - Nuxt.js stores all data in `window.__NUXT__`
   - Extracts `hData` (house data) from the structure
   - Handles different JSON structures gracefully

4. **Extract FAQs from DOM** (fallback)
   - If FAQs not in `__NUXT__`, extracts from DOM
   - Looks for `div.faq-item` elements
   - Parses question/answer pairs

5. **Extract Structured Data**
   - Media array (images, videos, VR links, lives, by tenants)
   - Room types with tenancies
   - Payment details, offers, amenities
   - Cancellation policies, FAQs

6. **Convert to Markdown**
   - Converts JSON to markdown format
   - Compatible with existing analysis pipeline

### Retry Logic

- **Max Retries:** 2 attempts
- **Retry Conditions:**
  - Timeout exceptions
  - WebDriver exceptions
  - `__NUXT__` not found

### Data Structure

```python
{
    'success': True,
    'url': 'https://en.uhomes.com/uk/...',
    'markdown': '# Property Name\n\n...',
    'metadata': {
        'title': 'Property Name',
        'images': [...],
        'videos': [...],
        'virtual_tours': [...],
        'room_types': [...],
        'hero_features': {...},
        'payment_details': {...},
        'offers': [...]
    },
    'raw_json': {...}  # Full hData from __NUXT__
}
```

---

## Media Extraction

### Images

**Amber:**
- From `data.images` array
- Includes room type images (fetched separately)

**UHomes:**
- From `media` array (type: "image")
- Uses `count` field (matches website display)
- Includes room type images

### Videos

**Amber:**
- From `data.videos` array
- Includes video tours

**UHomes:**
- From `media` array (type: "video")
- Uses `count` field
- Includes digital human videos

### Virtual Tours

**Amber:**
- From `data.virtual_views` array
- Separates 360° and 3D tours

**UHomes:**
- From `media` array (type: "vr_link")
- Uses `count` field
- Also from room types

### Lives & By Tenants (UHomes Only)

- **Lives:** From `media` array (type: "live")
- **By Tenants:** From `media` array (type: "by_tenant")
- Uses `count` field for accurate counts

---

## Error Handling

### Amber Scraper Errors

- **Invalid URL:** Raises `ValueError`
- **API Failure:** Returns `{'success': False, 'error': '...'}`
- **Network Issues:** Handled by `requests` library

### UHomes Scraper Errors

- **Browser Launch Failure:** Raises `ImportError` or `WebDriverException`
- **Page Load Timeout:** Retries up to 2 times
- **`__NUXT__` Not Found:** Retries with extended wait
- **DOM Extraction Failure:** Falls back gracefully

---

## Rate Limiting

- **Between Properties:** 5-10 seconds random delay
- **Between Platforms:** 5-10 seconds random delay
- **Purpose:** Avoid overwhelming APIs and websites

---

## Backup Files

All scraped data is backed up:

**JSON Backups:**
- Location: `scraped_json_backup/`
- Format: `{Property_ID}_{platform}_raw.json`
- Contains: Full raw JSON response

**Markdown Backups:**
- Location: `scraped_data_backup/`
- Format: `{Property_ID}_{platform}_full.md`
- Contains: Converted markdown content

---

## Troubleshooting

### Amber Scraping Fails

1. **Check URL format:** Must be valid Amber URL
2. **Check API endpoint:** Verify API is accessible
3. **Check network:** Ensure internet connection
4. **Check logs:** Look for specific error messages

### UHomes Scraping Fails

1. **Check Chrome:** Ensure Chrome browser is installed
2. **Check URL:** Verify UHomes URL is accessible
3. **Check timeout:** Increase timeout if page loads slowly
4. **Check `__NUXT__`:** Verify JavaScript executed (check logs)
5. **Check retries:** System retries automatically (check logs)

### Common Issues

**"Chrome not found"**
- Install Chrome browser
- Or set Chrome binary path in code

**"__NUXT__ not found"**
- Page may not have loaded completely
- Check network connection
- Verify URL is correct

**"Timeout"**
- Page may be loading slowly
- Increase timeout in code
- Check internet connection

---

## Code Examples

### Scraping a Single Property

```python
from src.scrapers.amber_api_scraper import AmberAPIScraper
from src.scrapers.uhomes_puppeteer_scraper import UHomesPuppeteerScraper

# Amber
amber_scraper = AmberAPIScraper()
amber_result = amber_scraper.scrape_url('https://amberstudent.com/places/...')

# UHomes
uhomes_scraper = UHomesPuppeteerScraper(use_playwright=False)
uhomes_result = uhomes_scraper.scrape_url('https://en.uhomes.com/uk/...')
```

### Using Scraper Factory

```python
from src.scrapers.scraper_factory import ScraperFactory

factory = ScraperFactory(prefer_api=True)
result = factory.scrape_url('https://amberstudent.com/places/...')
```

---

## Next Steps

After scraping:
1. Data is stored in `Raw_Scraped_Data` sheet
2. Proceed to **Extraction** step: `run_extraction_step1.py`
3. See [Extraction Guide](02_EXTRACTION.md) for details

---

**Related Documentation:**
- [Extraction Guide](02_EXTRACTION.md)
- [Architecture Guide](05_ARCHITECTURE.md)
