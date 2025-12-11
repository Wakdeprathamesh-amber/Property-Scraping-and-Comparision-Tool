# Google Sheets Usage Analysis

## Summary

**Required Sheets:** 4  
**Unused Sheets:** 5  
**Total Sheets Defined:** 7

---

## ✅ REQUIRED SHEETS (Currently Used)

These sheets are **actively used** in the current pipeline and **MUST NOT be deleted**:

### 1. `Input_Properties` ✅ REQUIRED
- **Purpose:** Input sheet where properties are added
- **Used By:**
  - `run_scraper_api_only.py` - Reads pending properties
  - `run_extraction_step1.py` - Reads scraped properties
  - `v0_property_comparison.py` - Reads scraped properties
  - `clear_and_rerun_all.py` - Reads properties
  - `csv_processor.py` - Writes properties from CSV
- **Columns:** Property_ID, Amber_URL, Uhomes_URL, Status, Created_At
- **Status:** ✅ **KEEP - CRITICAL**

### 2. `Raw_Scraped_Data` ✅ REQUIRED
- **Purpose:** Stores raw scraped data from both platforms
- **Used By:**
  - `run_scraper_api_only.py` - Writes scraped data
  - `run_extraction_step1.py` - Reads scraped data for extraction
  - `bulk_scraper.py` - Writes scraped data
- **Columns:** Property_ID, Platform, Property_Name, Raw_JSON_Data, Markdown_Content, etc.
- **Status:** ✅ **KEEP - CRITICAL**

### 3. `Content_Extraction` ✅ REQUIRED
- **Purpose:** Stores extracted structured content for all 10 sections
- **Used By:**
  - `run_extraction_step1.py` - Writes extracted content
  - `v0_property_comparison.py` - Reads extracted content for comparison
  - `clear_and_rerun_all.py` - Reads/clears extraction data
- **Columns:** Property_ID, Platform, Section_Name, Content_JSON, Item_Count, etc.
- **Status:** ✅ **KEEP - CRITICAL**

### 4. `V0_Comparison_Results` ✅ REQUIRED
- **Purpose:** Stores side-by-side comparison results
- **Used By:**
  - `v0_property_comparison.py` - Writes comparison results
  - `clear_and_rerun_all.py` - Reads/clears comparison data
- **Columns:** Hierarchical headers (3 rows) with comparison metrics
- **Status:** ✅ **KEEP - CRITICAL**

---

## ❌ UNUSED SHEETS (Can Be Deleted)

These sheets are **defined in `setup_sheet_headers.py`** but **NOT used** in the current pipeline. They appear to be from an older version that used scoring/insights.

### 1. `Section_Scores` ❌ UNUSED
- **Purpose:** Was meant to store section-level scores
- **Used By:** ❌ **NOT USED ANYWHERE**
- **Reason:** Current pipeline doesn't use scoring (V0 = no scoring)
- **Status:** ❌ **CAN DELETE**

### 2. `Property_Comparisons` ❌ UNUSED
- **Purpose:** Was meant to store property-level comparison scores
- **Used By:** ❌ **NOT USED ANYWHERE**
- **Reason:** Replaced by `V0_Comparison_Results` (simpler, no scoring)
- **Status:** ❌ **CAN DELETE**

### 3. `Insights_Recommendations` ❌ UNUSED
- **Purpose:** Was meant to store AI-generated insights and recommendations
- **Used By:** ❌ **NOT USED ANYWHERE**
- **Reason:** Current V0 pipeline doesn't generate insights
- **Status:** ❌ **CAN DELETE**

### 4. `Exclusive_Features` ❌ UNUSED
- **Purpose:** Was meant to store features unique to one platform
- **Used By:** ❌ **NOT USED ANYWHERE**
- **Reason:** Not implemented in current pipeline
- **Status:** ❌ **CAN DELETE**

### 5. `Section_Details` ❌ UNUSED
- **Purpose:** Was meant to store detailed subsection data
- **Used By:** ❌ **NOT USED ANYWHERE**
- **Reason:** Not implemented in current pipeline
- **Status:** ❌ **CAN DELETE**

---

## 📋 Recommended Action

### Safe to Delete (5 sheets):
1. ✅ `Section_Scores`
2. ✅ `Property_Comparisons`
3. ✅ `Insights_Recommendations`
4. ✅ `Exclusive_Features`
5. ✅ `Section_Details`

### Must Keep (4 sheets):
1. ✅ `Input_Properties`
2. ✅ `Raw_Scraped_Data`
3. ✅ `Content_Extraction`
4. ✅ `V0_Comparison_Results`

---

## 🔧 Optional: Clean Up `setup_sheet_headers.py`

After deleting unused sheets, you can optionally update `setup_sheet_headers.py` to remove the unused sheet setup code. However, this is **not required** - the script will just skip sheets that don't exist.

---

## ⚠️ Important Notes

1. **Backup First:** Before deleting sheets, make sure you have a backup of your Google Sheet
2. **No Data Loss:** The unused sheets don't contain data from the current pipeline, so deleting them is safe
3. **Future Use:** If you plan to add scoring/insights features later, you might want to keep the sheet definitions (but can delete the actual sheets)

---

## ✅ Verification

After deletion, verify the pipeline still works:
```bash
# Test the pipeline
python3 clear_and_rerun_all.py --yes
```

The pipeline should work perfectly with just the 4 required sheets.
