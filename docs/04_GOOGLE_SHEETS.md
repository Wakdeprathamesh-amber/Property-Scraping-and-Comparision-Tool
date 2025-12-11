# Google Sheets Guide

This document explains the Google Sheets structure and how to use it.

---

## Overview

The pipeline uses Google Sheets for data storage and visualization. All data flows through 4 main sheets.

---

## Required Sheets

### 1. Input_Properties

**Purpose:** Input sheet where properties are added for processing.

**Columns:**
- `Property_ID` - Unique identifier (e.g., P001, P002)
- `Amber_URL` - Full Amber property URL
- `Uhomes_URL` - Full UHomes property URL
- `Status` - Processing status: 'pending', 'processing', 'scraped', 'partial', 'failed'
- `Created_At` - Timestamp when property was added

**Usage:**
1. Add new properties with `Status = 'pending'`
2. Pipeline automatically processes pending properties
3. Status updates automatically as pipeline progresses

**Example:**
```
Property_ID | Amber_URL                                    | Uhomes_URL                                    | Status  | Created_At
P001        | https://amberstudent.com/places/...         | https://en.uhomes.com/uk/...                | scraped | 2024-12-08
P002        | https://amberstudent.com/places/...         | https://en.uhomes.com/uk/...                | pending | 2024-12-08
```

---

### 2. Raw_Scraped_Data

**Purpose:** Stores raw scraped data from both platforms.

**Columns:**
- `Property_ID` - Property identifier
- `Platform` - 'amber' or 'uhomes'
- `Property_Name` - Property name
- `City` - City name
- `Country` - Country (usually 'UK')
- `Markdown_Content` - Converted markdown content
- `Raw_JSON_Data` - Full raw JSON response (may be truncated)
- `Metadata_JSON` - Basic metadata
- `Hero_Features_JSON` - Hero section features
- `Payment_Details_JSON` - Payment details
- `Offers_JSON` - Offers/promotions
- `Nearby_Properties_JSON` - Nearby properties
- `Room_Types_JSON` - Room types data
- `Property_Metadata_JSON` - Additional metadata
- `Videos_JSON` - Videos list
- `Virtual_Tours_JSON` - Virtual tours list
- `Images_Count` - Image count
- `Images_URLs` - First 10 image URLs
- `Videos_Count` - Video count
- `Virtual_Tours_Count` - Virtual tour count
- `Links_Count` - Link count
- `Word_Count` - Word count
- `Scraper_Used` - Which scraper was used
- `Scraped_At` - Timestamp

**Usage:**
- Read-only (populated by scraping step)
- Contains raw data for debugging
- Full JSON available in backup files if truncated

**Note:** Each property has 2 rows (one for Amber, one for UHomes).

---

### 3. Content_Extraction

**Purpose:** Stores extracted structured content for all 10 sections.

**Columns:**
- `Property_ID` - Property identifier
- `Platform` - 'amber' or 'uhomes'
- `Property_Name` - Property name
- `Section_Name` - One of 10 sections
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

**Usage:**
- Read-only (populated by extraction step)
- Contains structured extracted data
- Used by comparison step

**Note:** Each property has 20 rows (10 sections × 2 platforms).

**Sections:**
1. Hero & Media
2. Offers
3. About Property
4. Room Types
5. Amenities
6. Payment
7. Cancellation
8. FAQs
9. Nearby Properties
10. University Links

---

### 4. V0_Comparison_Results

**Purpose:** Side-by-side comparison of Amber vs UHomes.

**Structure:**
- **3 Header Rows:**
  - Row 1: Section names (merged)
  - Row 2: Sub-section names (merged)
  - Row 3: Platform names (Amber | UHomes)

- **Data Rows:** One row per property starting from row 4

**Columns:**
- Property_ID
- Property_Name
- Link (Amber URL)
- Hero & Media metrics (Images, Videos, Virtual Tours, Lives, By Tenants)
- Offers count
- About Property word count
- Room Types metrics (Count, Available Tenancies, Total Tenancies, Category breakdowns)
- Amenities metrics (Count, Unique to UHomes)
- Payment metrics (Installment Options, Payment Methods, Guarantor)
- Cancellation metrics (Has Policy, Policy Count)
- FAQs count
- Nearby Properties count
- University Links count
- Total Improvement Areas

**Usage:**
- Read-only (populated by comparison step)
- Used for analysis and identifying improvement areas
- Set up conditional formatting manually

**Conditional Formatting:**
- Red: Where UHomes > Amber (improvement needed)
- Green: Where Amber > UHomes (doing well)
- Freeze: First 3 columns

---

## Unused Sheets (Can Be Deleted)

These sheets are defined but not used in the current pipeline:

1. `Section_Scores` - Old scoring system
2. `Property_Comparisons` - Old comparison system
3. `Insights_Recommendations` - Not implemented
4. `Exclusive_Features` - Not implemented
5. `Section_Details` - Not implemented

See [SHEETS_USAGE_ANALYSIS.md](../SHEETS_USAGE_ANALYSIS.md) for details.

---

## Setup

### Initial Setup

1. **Create Google Sheet**
   - Name: `Property_Comparison_Data`
   - Create in Google Drive

2. **Set Up Service Account**
   - Go to Google Cloud Console
   - Create service account
   - Download credentials JSON
   - Save as `credentials.json` in project root

3. **Share Sheet**
   - Share Google Sheet with service account email
   - Give "Editor" permissions

4. **Run Setup Script**
   ```bash
   python3 setup_sheet_headers.py
   ```
   This creates all required sheets with proper headers.

---

## Data Flow

```
Input_Properties (add properties)
    ↓
[Scraping]
    ↓
Raw_Scraped_Data (raw data)
    ↓
[Extraction]
    ↓
Content_Extraction (structured data)
    ↓
[Comparison]
    ↓
V0_Comparison_Results (comparison metrics)
```

---

## Best Practices

### Adding Properties

1. **Use Consistent IDs**
   - Format: P001, P002, P003, etc.
   - No spaces or special characters

2. **Verify URLs**
   - Test URLs before adding
   - Ensure URLs are accessible

3. **Set Status Correctly**
   - New properties: `Status = 'pending'`
   - Don't manually change status (pipeline handles it)

### Viewing Results

1. **Freeze Headers**
   - Freeze first 3 rows in V0_Comparison_Results
   - Freeze first column for Property_ID

2. **Use Filters**
   - Add filters to header rows
   - Filter by Property_ID, Platform, Section_Name

3. **Conditional Formatting**
   - Set up red/green formatting
   - Highlight improvement areas

### Data Management

1. **Backup Regularly**
   - Export sheets periodically
   - Keep backup of important data

2. **Don't Edit Generated Data**
   - Raw_Scraped_Data: Read-only
   - Content_Extraction: Read-only
   - V0_Comparison_Results: Read-only

3. **Clear Old Data**
   - Use `clear_and_rerun_all.py` to clear old extraction/comparison data
   - Keeps Raw_Scraped_Data (for reference)

---

## Troubleshooting

### "Spreadsheet not found"
- Check sheet name: `Property_Comparison_Data`
- Verify service account has access
- Check credentials.json is correct

### "Sheet not found"
- Run `setup_sheet_headers.py` to create sheets
- Check sheet names match exactly (case-sensitive)

### "Permission denied"
- Share sheet with service account email
- Give "Editor" permissions
- Check credentials.json is valid

### "Data not updating"
- Check pipeline is running
- Verify status in Input_Properties
- Check logs for errors

---

## API Limits

Google Sheets API has limits:
- **100 requests per 100 seconds per user**
- **10 requests per second per user**

The pipeline includes delays to avoid hitting limits:
- 1-2 seconds between sheet operations
- 5-10 seconds between properties

---

## Backup Files

All scraped data is backed up locally:

**JSON Backups:**
- Location: `scraped_json_backup/`
- Format: `{Property_ID}_{platform}_raw.json`
- Contains: Full raw JSON (not truncated)

**Markdown Backups:**
- Location: `scraped_data_backup/`
- Format: `{Property_ID}_{platform}_full.md`
- Contains: Converted markdown content

**Use Cases:**
- If sheet data is truncated, use backup files
- For debugging and analysis
- For data recovery

---

## Related Documentation

- [Scraping Guide](01_SCRAPING.md)
- [Extraction Guide](02_EXTRACTION.md)
- [V0 Comparison Guide](03_V0_COMPARISON.md)
- [Architecture Guide](05_ARCHITECTURE.md)
