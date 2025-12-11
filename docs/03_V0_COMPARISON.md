# V0 Comparison Guide

This document explains how the V0 comparison tool works and generates comparison results.

---

## Overview

The V0 comparison tool compares extracted content between Amber and UHomes platforms. It's designed to be **simple, focused, and easy to understand** - showing property-level differences without complex scoring.

---

## Entry Point

**File:** `v0_property_comparison.py`

**Usage:**
```bash
# Compare all properties
python3 v0_property_comparison.py

# Compare specific property
python3 v0_property_comparison.py P001
```

---

## How It Works

### Step 1: Read Extracted Content

Reads from `Content_Extraction` Google Sheet:
- Filters for property
- Separates Amber and UHomes data
- Groups by section

### Step 2: Compare Sections

For each of 10 sections:
1. Extracts metrics from both platforms
2. Compares values
3. Identifies differences
4. Tracks improvement areas (where UHomes is better)

### Step 3: Generate Results

Creates comparison dictionary:
- Section-by-section comparison
- Summary metrics
- Improvement area tracking

### Step 4: Write to Sheets

Writes to `V0_Comparison_Results` Google Sheet:
- Hierarchical headers (3 rows)
- Side-by-side comparison
- Total improvement areas count

---

## Comparison Logic

### Hero & Media Comparison

**Metrics Compared:**
- Image count
- Video count
- Virtual tour count
- Live count (UHomes only)
- By tenant count (UHomes only)

**Improvement Tracking:**
- If UHomes has more images → improvement needed
- If UHomes has more videos → improvement needed
- If UHomes has more virtual tours → improvement needed

### Room Types Comparison

**Metrics Compared:**
- Room type count
- Available tenancies (matches website display)
- Total tenancies (all inventory)
- Available tenancies by category (Studio/Ensuite/Non Ensuite)

**Improvement Tracking:**
- If UHomes has more room types → improvement needed
- If UHomes has more available tenancies → improvement needed
- If UHomes has more in any category → improvement needed

### Amenities Comparison

**Metrics Compared:**
- Amenity count (property-level only)
- Unique amenities (only in UHomes)

**Improvement Tracking:**
- If UHomes has more amenities → improvement needed
- If UHomes has unique amenities → improvement needed

**Normalization:**
- Case-insensitive matching
- Removes special characters
- Normalizes whitespace

### Payment Comparison

**Metrics Compared:**
- Installment options count
- Payment methods count
- Guarantor requirement

**Improvement Tracking:**
- If UHomes has more installment options → improvement needed
- If UHomes has more payment methods → improvement needed
- If UHomes doesn't require guarantor (but Amber does) → improvement needed

### Other Sections

**Offers:** Compares offer count  
**About Property:** Compares word count  
**Cancellation:** Compares policy existence and count  
**FAQs:** Compares FAQ count  
**Nearby Properties:** Compares property count  
**University Links:** Compares university count  

---

## V0_Comparison_Results Sheet Structure

### Hierarchical Headers (3 Rows)

**Row 1:** Section names (merged across columns)
- Hero & Media, Offers, About Property, Room Types, Amenities, Payment, Cancellation, FAQs, Nearby Properties, University Links

**Row 2:** Sub-section names
- Images, Videos, Virtual Tours, Lives, By Tenants
- Count, Word Count, Room Type Count, Available Tenancies, etc.

**Row 3:** Platform names
- Amber | UHomes (alternating)

### Data Columns

**Property Info:**
- Property_ID
- Property_Name
- Link (Amber URL)

**Hero & Media (5 columns):**
- Images: Amber | UHomes
- Videos: Amber | UHomes
- Virtual Tours: Amber | UHomes
- Lives: Amber | UHomes
- By Tenants: Amber | UHomes

**Offers (2 columns):**
- Count: Amber | UHomes

**About Property (2 columns):**
- Word Count: Amber | UHomes

**Room Types (12 columns):**
- Room Type Count: Amber | UHomes
- Available Tenancies: Amber | UHomes
- Total Tenancies: Amber | UHomes
- Studio Available: Amber | UHomes
- Ensuite Available: Amber | UHomes
- Non Ensuite Available: Amber | UHomes

**Amenities (4 columns):**
- Count: Amber | UHomes
- Unique to UHomes Count
- Only in UHomes (JSON List)

**Payment (6 columns):**
- Installment Options: Amber | UHomes
- Payment Methods: Amber | UHomes
- Guarantor Required: Amber | UHomes

**Cancellation (4 columns):**
- Has Policy: Amber | UHomes
- Policy Count: Amber | UHomes

**FAQs (2 columns):**
- Count: Amber | UHomes

**Nearby Properties (2 columns):**
- Count: Amber | UHomes

**University Links (2 columns):**
- Count: Amber | UHomes

**Total Improvement Areas (1 column):**
- Sum of all improvement areas across sections

---

## Improvement Area Tracking

### What Counts as Improvement Area?

An improvement area is identified when:
- UHomes has a **higher count** than Amber
- UHomes has **unique content** that Amber lacks
- UHomes has **better features** (e.g., no guarantor required)

### Total Improvement Areas

Sum of all improvement areas across all sections:
- Each section can contribute multiple improvement areas
- Example: Room Types section can contribute:
  - Room Type Count (if UHomes > Amber)
  - Available Tenancies (if UHomes > Amber)
  - Studio Available (if UHomes > Amber)
  - Ensuite Available (if UHomes > Amber)
  - Non Ensuite Available (if UHomes > Amber)

---

## Comparison Output

### Text Report

Generate human-readable report:
```python
from v0_property_comparison import V0PropertyComparison

comparator = V0PropertyComparison()
report = comparator.generate_report('P001', output_format='text')
print(report)
```

**Report Includes:**
- Property information
- Summary metrics
- Key differences
- Section-by-section details

### JSON Output

Generate JSON report:
```python
report = comparator.generate_report('P001', output_format='json')
```

**JSON Structure:**
```json
{
  "property_id": "P001",
  "property_name": "Property Name",
  "compared_at": "2024-12-08 16:00:00",
  "sections": {
    "Hero & Media": {
      "amber": {...},
      "uhomes": {...},
      "differences": [...],
      "improvement_needed": [...],
      "uhomes_better_count": 2
    },
    ...
  },
  "summary": {...}
}
```

---

## Cell Merging

### Section Headers (Row 1)

Merged across all columns for that section:
- Hero & Media: Merged across 10 columns (5 sub-sections × 2 platforms)
- Room Types: Merged across 12 columns
- Amenities: Merged across 4 columns
- etc.

### Sub-Section Headers (Row 2)

Merged across 2 columns (Amber | UHomes):
- Images: Merged across 2 columns
- Videos: Merged across 2 columns
- etc.

### Total Improvement Areas

Merged across all 3 rows (single column).

---

## Conditional Formatting (Manual)

After running comparison, set up conditional formatting in Google Sheets:

**Red:** Where UHomes value > Amber value (improvement needed)  
**Green:** Where Amber value > UHomes value (doing well)  
**Freeze:** First 3 columns (Property_ID, Property_Name, Link)

---

## Usage Examples

### Compare All Properties

```python
from v0_property_comparison import V0PropertyComparison

comparator = V0PropertyComparison()
comparisons = comparator.compare_all_properties(write_to_sheets=True)
```

### Compare Single Property

```python
comparison = comparator.compare_property('P001')
print(f"Improvement areas: {comparison['summary']}")
```

### Generate Report

```python
report = comparator.generate_report('P001')
print(report)
```

---

## Troubleshooting

### "No content found"
- Check `Content_Extraction` sheet has data
- Verify property ID is correct
- Check both platforms have data

### "Missing platform data"
- Ensure both Amber and UHomes data exists
- Check extraction completed successfully
- Verify platform names are 'amber' and 'uhomes'

### "Sheet merge errors"
- Merging is optional (data still written)
- Can merge manually in Google Sheets
- Check logs for specific errors

---

## Key Features

### Simple & Focused
- No complex scoring
- Easy to understand metrics
- Clear improvement areas

### Accurate Comparison
- Uses extracted content (not raw data)
- Normalizes data for fair comparison
- Handles missing data gracefully

### Actionable Insights
- Identifies specific improvement areas
- Shows exact differences
- Tracks "UHomes better" metrics

---

## Next Steps

After comparison:
1. Results are in `V0_Comparison_Results` sheet
2. Review comparison metrics
3. Identify improvement priorities
4. Take action on improvement areas

---

**Related Documentation:**
- [Extraction Guide](02_EXTRACTION.md)
- [Google Sheets Guide](04_GOOGLE_SHEETS.md)
- [Architecture Guide](05_ARCHITECTURE.md)
