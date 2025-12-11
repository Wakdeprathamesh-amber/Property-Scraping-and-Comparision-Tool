# Property-Content-Goldmine

**A comprehensive pipeline for comparing property listings between Amber and UHomes platforms**

Automatically scrapes, extracts structured content, and compares property data to identify gaps and improvement opportunities.

---

## 🎯 Overview

Property-Content-Goldmine is a production-ready pipeline that:

- ✅ **Scrapes** property data from Amber API and UHomes using browser automation
- ✅ **Extracts** structured content from 10 key sections (Hero & Media, Room Types, Amenities, Payment, etc.)
- ✅ **Compares** properties side-by-side to identify differences and improvement areas
- ✅ **Stores** all data in Google Sheets for easy analysis and visualization

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud Service Account (for Google Sheets API)
- Chrome browser (for UHomes scraping)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Wakdeprathamesh-amber/Property-Content-Goldmine.git
   cd Property-Content-Goldmine
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Sheets**
   - Create a Google Sheet named `Property_Comparison_Data`
   - Create a Google Cloud Service Account
   - Download credentials JSON and save as `credentials.json` in project root
   - Share the Google Sheet with the service account email

4. **Configure sheets** (first time setup)
   ```bash
   python3 setup_sheet_headers.py
   ```

5. **Add properties** to `Input_Properties` sheet:
   - `Property_ID` (e.g., P001)
   - `Amber_URL` 
   - `Uhomes_URL`
   - `Status` (set to 'pending')

6. **Run the pipeline**
   ```bash
   python3 clear_and_rerun_all.py
   ```
   When prompted, type `yes` to continue.

---

## 📊 Pipeline Flow

```
Input_Properties (Google Sheet)
    ↓
[1] Scraping (run_scraper_api_only.py)
    ↓
Raw_Scraped_Data (Google Sheet)
    ↓
[2] Extraction (run_extraction_step1.py)
    ↓
Content_Extraction (Google Sheet)
    ↓
[3] V0 Comparison (v0_property_comparison.py)
    ↓
V0_Comparison_Results (Google Sheet)
```

### Step-by-Step Execution

**Step 1: Scraping**
```bash
python3 run_scraper_api_only.py
```
- Scrapes properties from both platforms
- Stores raw JSON data in `Raw_Scraped_Data` sheet
- Creates backup files in `scraped_json_backup/`

**Step 2: Extraction**
```bash
python3 run_extraction_step1.py
```
- Extracts structured content from raw scraped data
- Processes 10 sections per property
- Stores extracted content in `Content_Extraction` sheet

**Step 3: Comparison**
```bash
python3 v0_property_comparison.py
```
- Compares Amber vs UHomes for each property
- Generates side-by-side comparison in `V0_Comparison_Results` sheet
- Highlights differences and improvement areas

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Scraping Guide](docs/01_SCRAPING.md)** - How scraping works for both platforms
- **[Extraction Guide](docs/02_EXTRACTION.md)** - Content extraction process and sections
- **[V0 Comparison Guide](docs/03_V0_COMPARISON.md)** - Comparison logic and results
- **[Google Sheets Guide](docs/04_GOOGLE_SHEETS.md)** - Sheets structure and usage
- **[Architecture Guide](docs/05_ARCHITECTURE.md)** - Codebase structure and design

---

## 🔧 Core Components

### Scrapers (`src/scrapers/`)

- **`amber_api_scraper.py`** - Direct API calls to Amber's API
- **`uhomes_puppeteer_scraper.py`** - Browser automation to extract UHomes data
- **`scraper_factory.py`** - Factory pattern for scraper selection

### Extractors (`src/`)

- **`rule_based_extractor.py`** - Rule-based extraction from JSON data
- **`run_extraction_step1.py`** - Main extraction orchestrator

### Comparators

- **`v0_property_comparison.py`** - V0 comparison tool (simple, no scoring)

### Utilities

- **`sheets_manager.py`** - Google Sheets API integration
- **`utils/logger.py`** - Structured logging

---

## 📈 Google Sheets Structure

### Required Sheets

1. **`Input_Properties`** - Input properties with URLs
2. **`Raw_Scraped_Data`** - Raw scraped JSON data
3. **`Content_Extraction`** - Extracted structured content
4. **`V0_Comparison_Results`** - Side-by-side comparison results

See [SHEETS_USAGE_ANALYSIS.md](SHEETS_USAGE_ANALYSIS.md) for details on which sheets are used.

---

## 🔍 Extracted Sections

The pipeline extracts content from 10 key sections:

1. **Hero & Media** - Images, videos, virtual tours, lives
2. **Offers** - Promotions and special offers
3. **About Property** - Property descriptions and details
4. **Room Types** - Room categories, tenancies, availability
5. **Amenities** - Property-level amenities
6. **Payment** - Installment options, payment methods, guarantor
7. **Cancellation** - Cancellation policies
8. **FAQs** - Frequently asked questions
9. **Nearby Properties** - Similar/recommended properties
10. **University Links** - Nearby universities and distances

---

## 🎯 Key Features

### Accurate Media Counting
- **Images**: Hero + room type images
- **Videos**: Regular videos + video tours
- **Virtual Tours**: 360° and 3D tours separately
- **Lives**: Live video content (UHomes)
- **By Tenants**: Tenant-uploaded media (UHomes)

### Room Type Analysis
- Categorization: Studio, Ensuite, Non Ensuite
- Tenancy tracking: Available vs Total
- Category-level counts
- Individual room type details

### Comparison Metrics
- Side-by-side comparison
- Difference identification
- Improvement area tracking
- "UHomes better" metrics

---

## 🛠️ Development

### Project Structure

```
Property-Content-Goldmine/
├── run_scraper_api_only.py      # Step 1: Scraping
├── run_extraction_step1.py      # Step 2: Extraction
├── v0_property_comparison.py    # Step 3: Comparison
├── clear_and_rerun_all.py      # Main orchestrator
├── setup_sheet_headers.py       # Sheet setup utility
│
├── src/
│   ├── scrapers/                # API scrapers
│   │   ├── amber_api_scraper.py
│   │   ├── uhomes_puppeteer_scraper.py
│   │   └── scraper_factory.py
│   ├── rule_based_extractor.py  # Content extraction
│   ├── sheets_manager.py        # Google Sheets integration
│   └── utils/                   # Logger and utilities
│
├── docs/                        # Documentation
├── scraped_json_backup/        # Backup JSON files
├── scraped_data_backup/        # Backup markdown files
└── requirements.txt             # Dependencies
```

### Adding New Properties

1. Add row to `Input_Properties` sheet:
   - `Property_ID`: Unique identifier (e.g., P001)
   - `Amber_URL`: Full Amber property URL
   - `Uhomes_URL`: Full UHomes property URL
   - `Status`: Set to `'pending'`

2. Run pipeline:
   ```bash
   python3 clear_and_rerun_all.py
   ```

3. Check results in `V0_Comparison_Results` sheet

---

## 🐛 Troubleshooting

### "Spreadsheet not found"
- Share Google Sheet with service account email
- Check sheet name matches `Property_Comparison_Data`
- Verify `credentials.json` is in project root

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.8+)

### "Content_JSON too large"
- System automatically optimizes large JSON data
- Full data available in backup JSON files (`scraped_json_backup/`)

### UHomes scraping fails
- Ensure Chrome browser is installed
- Check internet connection
- Verify UHomes URL is accessible

---

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary and confidential.

---

## 👥 Team

- **Repository**: [Property-Content-Goldmine](https://github.com/Wakdeprathamesh-amber/Property-Content-Goldmine)
- **Maintained by**: Amber Team

---

## 📚 Additional Resources

- [Code Review Report](CODE_REVIEW_REPORT.md) - Comprehensive code review
- [Sheets Usage Analysis](SHEETS_USAGE_ANALYSIS.md) - Google Sheets usage guide
- [Documentation](docs/) - Detailed technical documentation

---

**Version**: 3.0 (Clean Pipeline)  
**Last Updated**: December 2024
