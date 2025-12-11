# Extraction Guide

This document explains how content extraction works from scraped data.

---

## Overview

The extraction module processes raw scraped data and extracts structured content from 10 key sections. It uses **rule-based extraction** (no AI) for accuracy and reliability.

---

## Entry Point

**File:** `run_extraction_step1.py`

**Usage:**
```bash
python3 run_extraction_step1.py
```

---

## How It Works

### Step 1: Read Scraped Data

Reads from `Raw_Scraped_Data` Google Sheet:
- Filters for scraped properties
- Loads raw JSON data from sheet or backup files

### Step 2: Extract Content

For each property and platform:
1. Loads API data (from sheet or backup)
2. Extracts structured data from JSON columns
3. Runs rule-based extraction
4. Extracts all 10 sections

### Step 3: Store Results

Writes to `Content_Extraction` Google Sheet:
- One row per section per platform
- Stores full content as JSON
- Includes counts and metadata

---

## Extracted Sections

### 1. Hero & Media

**What's Extracted:**
- Image count (hero + room types)
- Video count (including video tours)
- Virtual tour count (360° and 3D separately)
- Live count (UHomes only)
- By tenant count (UHomes only)
- Map availability
- Price display

**Data Structure:**
```json
{
  "image_count": 96,
  "video_count": 15,
  "virtual_tour_count": 12,
  "tour_360_count": 10,
  "tour_3d_count": 2,
  "live_count": 2,
  "by_tenant_count": 5,
  "has_map": true,
  "has_price_display": true
}
```

### 2. Offers

**What's Extracted:**
- Offer count
- Offer list with details
- Offer types

**Data Structure:**
```json
{
  "offer_count": 2,
  "offers": [
    {"name": "Cashback", "amount": 50, "type": "cashback"},
    {"name": "Early Bird", "description": "..."}
  ]
}
```

### 3. About Property

**What's Extracted:**
- Word count
- Full description text
- Highlights
- Tags
- Location details
- Property info (unit count, area, etc.)

**Data Structure:**
```json
{
  "word_count": 450,
  "content": "Full description text...",
  "has_content": true,
  "highlights": [...],
  "tags": [...],
  "location": {...},
  "property_info": {...}
}
```

### 4. Room Types

**What's Extracted:**
- Room type count
- Individual room types with details
- Category counts (Studio, Ensuite, Non Ensuite)
- Total tenancies
- Available tenancies
- Tenancy counts per category
- Room type media counts

**Data Structure:**
```json
{
  "room_type_count": 21,
  "room_types": [
    {
      "name": "Gold Ensuite",
      "category": "Ensuite",
      "price": 150,
      "tenancies": [...],
      "tenancy_count": 5
    }
  ],
  "category_counts": {
    "Studio": 5,
    "Ensuite": 10,
    "Non Ensuite": 6
  },
  "total_tenancies": 150,
  "total_available_tenancies": 120,
  "category_tenancy_counts": {...},
  "category_available_tenancy_counts": {...}
}
```

### 5. Amenities

**What's Extracted:**
- Amenity count (property-level only)
- Amenity list
- All amenities (including room-level for reference)

**Data Structure:**
```json
{
  "amenity_count": 25,
  "amenities": ["WiFi", "Gym", "Pool", ...],
  "all_amenity_count": 45,
  "all_amenities": [...]
}
```

**Note:** For UHomes, only property-level amenities are counted (excludes Kitchen/Bedroom/Bathroom amenities).

### 6. Payment

**What's Extracted:**
- Installment options
- Payment methods
- Guarantor requirement
- Deposit details
- Holding fee
- Booking deposit
- Payment policy count

**Data Structure:**
```json
{
  "installment_options": [1, 2, 4],
  "payment_methods": ["Credit/Debit Card", "Bank Transfer"],
  "guarantor_required": false,
  "deposit": {"amount": 500, "currency": "GBP"},
  "has_deposit_info": true,
  "payment_policy_count": 4
}
```

### 7. Cancellation

**What's Extracted:**
- Has cancellation policy
- Policy text
- Policy details (cooling off, no visa no pay, etc.)
- Policy count

**Data Structure:**
```json
{
  "has_cancellation_policy": true,
  "policy_text": "Full policy text...",
  "detail_count": 3,
  "has_cooling_off": true,
  "has_no_visa_no_pay": true
}
```

### 8. FAQs

**What's Extracted:**
- FAQ count
- FAQ list (question/answer pairs)

**Data Structure:**
```json
{
  "faq_count": 8,
  "faqs": [
    {"question": "What is the minimum lease?", "answer": "..."},
    ...
  ]
}
```

### 9. Nearby Properties

**What's Extracted:**
- Property count
- Property list with details

**Data Structure:**
```json
{
  "property_count": 5,
  "properties": [
    {"name": "Property Name", "url": "...", "distance": "..."}
  ]
}
```

### 10. University Links

**What's Extracted:**
- University count
- University list with distances

**Data Structure:**
```json
{
  "university_count": 3,
  "universities": [
    {"name": "University Name", "distance": "0.5 miles"}
  ]
}
```

---

## Rule-Based Extraction

**File:** `src/rule_based_extractor.py`

### How It Works

1. **API Data Extraction**
   - Parses JSON structure directly
   - No AI/LLM dependencies
   - Fast and accurate

2. **Data Normalization**
   - Handles different data formats
   - Normalizes field names
   - Handles missing data gracefully

3. **Count Calculation**
   - Accurate counts from structured data
   - Deduplication where needed
   - Category grouping

### Platform-Specific Logic

**Amber:**
- Direct API structure access
- Fetches room types separately if needed
- Extracts from `data` object

**UHomes:**
- Extracts from `hData` structure
- Uses `count` fields for accurate counts
- Filters property-level amenities

---

## Data Storage

### Content_Extraction Sheet Structure

**Columns:**
- `Property_ID` - Property identifier
- `Platform` - 'amber' or 'uhomes'
- `Property_Name` - Property name
- `Section_Name` - Section name (one of 10 sections)
- `Content_JSON` - Full extracted content as JSON
- `Item_Count` - Count of items (amenities, FAQs, etc.)
- `Word_Count` - Word count for text sections
- `Image_Count` - Image count for media sections
- `Video_Count` - Video count
- `Virtual_Tour_Count` - Virtual tour count
- `Tenancy_Count` - Tenancy count (Room Types section)
- `Room_Category_Count` - Room category count (Room Types section)
- `Has_Content` - Boolean flag
- `Extracted_At` - Timestamp

### JSON Size Optimization

For large data (e.g., Room Types with many tenancies):
- Truncates tenancies if JSON > 50,000 chars
- Keeps essential fields only
- Creates summary if still too large
- Full data always available in backup files

---

## Room Type Categorization

**Categories:**
- **Studio** - Self-contained units
- **Ensuite** - Private bathroom
- **Non Ensuite** - Shared bathroom

**Categorization Logic:**
1. Check `type_id` (UHomes) or `unit_type` (Amber)
2. Check name patterns (case-insensitive)
3. Default to 'Unknown' if unclear

---

## Amenity Filtering (UHomes)

**Property-Level Amenities Only:**
- Sub-types: 11 (Safety), 55 (Property Services), 56 (Shared Community), 57 (Fitness & Recreation), 58 (Outdoor Features)

**Excluded (Room-Level):**
- Sub-types: 59 (General), 60 (Kitchen), 61 (Bedroom), 62 (Bathroom)

**Reason:** Only property-level amenities are shown on website and used for comparison.

---

## Error Handling

### Missing Data
- Returns empty/default values
- Logs warnings
- Continues processing

### JSON Parsing Errors
- Falls back to backup files
- Handles truncated JSON gracefully
- Logs errors for debugging

### Large Data
- Automatically optimizes JSON
- Truncates if needed
- Preserves essential data

---

## Troubleshooting

### "No API data available"
- Check `Raw_Scraped_Data` sheet has data
- Check backup files exist
- Verify scraping completed successfully

### "Content_JSON too large"
- System handles automatically
- Check backup files for full data
- Consider reducing tenancy details if needed

### "Missing sections"
- Check extraction logs
- Verify scraped data is complete
- Check for extraction errors

---

## Code Examples

### Extracting Content for One Property

```python
from run_extraction_step1 import ContentExtractor

extractor = ContentExtractor()
success = extractor.extract_property_content('P001')
```

### Processing All Scraped Properties

```python
from run_extraction_step1 import ContentExtractor

extractor = ContentExtractor()
stats = extractor.process_all_scraped()
# Returns: {'total': 3, 'success': 3, 'failed': 0}
```

---

## Next Steps

After extraction:
1. Data is stored in `Content_Extraction` sheet
2. Proceed to **Comparison** step: `v0_property_comparison.py`
3. See [V0 Comparison Guide](03_V0_COMPARISON.md) for details

---

**Related Documentation:**
- [Scraping Guide](01_SCRAPING.md)
- [V0 Comparison Guide](03_V0_COMPARISON.md)
- [Architecture Guide](05_ARCHITECTURE.md)
