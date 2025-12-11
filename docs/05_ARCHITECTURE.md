# Architecture Guide

This document explains the codebase structure and design patterns.

---

## Overview

Property-Content-Goldmine follows a clean, modular architecture with clear separation of concerns.

---

## Project Structure

```
Property-Content-Goldmine/
├── run_scraper_api_only.py      # Step 1: Scraping entry point
├── run_extraction_step1.py      # Step 2: Extraction entry point
├── v0_property_comparison.py    # Step 3: Comparison entry point
├── clear_and_rerun_all.py      # Main orchestrator
├── setup_sheet_headers.py       # Sheet setup utility
│
├── src/
│   ├── scrapers/                # Scraping modules
│   │   ├── __init__.py
│   │   ├── amber_api_scraper.py
│   │   ├── uhomes_puppeteer_scraper.py
│   │   ├── firecrawl_scraper.py (optional)
│   │   └── scraper_factory.py
│   │
│   ├── rule_based_extractor.py  # Content extraction logic
│   ├── sheets_manager.py        # Google Sheets integration
│   ├── bulk_scraper.py          # Bulk scraping utilities
│   ├── csv_processor.py         # CSV import utilities
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── property_data.py
│   │   └── section_data.py
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── logger.py            # Logging setup
│       └── llm_client.py        # LLM client (optional)
│
├── docs/                        # Documentation
│   ├── 01_SCRAPING.md
│   ├── 02_EXTRACTION.md
│   ├── 03_V0_COMPARISON.md
│   ├── 04_GOOGLE_SHEETS.md
│   └── 05_ARCHITECTURE.md
│
├── scraped_json_backup/        # Backup JSON files
├── scraped_data_backup/         # Backup markdown files
├── requirements.txt             # Python dependencies
├── README.md                    # Main documentation
└── .gitignore                   # Git ignore rules
```

---

## Architecture Patterns

### 1. Pipeline Pattern

The codebase follows a linear pipeline pattern:

```
Input → Scraping → Extraction → Comparison → Output
```

Each step:
- Reads from previous step's output
- Processes data
- Writes to next step's input
- Can run independently or together

### 2. Factory Pattern

**Scraper Factory** (`scraper_factory.py`):
- Chooses appropriate scraper based on platform
- Handles fallback logic
- Provides unified interface

### 3. Manager Pattern

**Sheets Manager** (`sheets_manager.py`):
- Encapsulates Google Sheets operations
- Provides clean API
- Handles authentication and errors

### 4. Rule-Based Extraction

**Rule-Based Extractor** (`rule_based_extractor.py`):
- No AI dependencies
- Fast and accurate
- Deterministic results

---

## Core Components

### Scrapers (`src/scrapers/`)

**AmberAPIScraper:**
- Direct API calls
- Fetches property data and room types
- Converts JSON to markdown

**UHomesPuppeteerScraper:**
- Browser automation (Selenium/Playwright)
- Extracts `window.__NUXT__` data
- Handles retries and timeouts

**ScraperFactory:**
- Platform detection
- Scraper selection
- Fallback handling

### Extractors (`src/`)

**RuleBasedExtractor:**
- Extracts counts from JSON
- Handles both platforms
- Deduplicates data

**ContentExtractor** (`run_extraction_step1.py`):
- Orchestrates extraction
- Processes all 10 sections
- Stores in Google Sheets

### Comparators

**V0PropertyComparison** (`v0_property_comparison.py`):
- Compares extracted content
- Generates comparison metrics
- Writes to Google Sheets

### Utilities

**SheetsManager:**
- Google Sheets API wrapper
- Authentication handling
- Batch operations

**Logger:**
- Structured logging
- File and console output
- Log levels

---

## Data Flow

### Scraping Flow

```
Input_Properties (Google Sheet)
    ↓
run_scraper_api_only.py
    ↓
AmberAPIScraper / UHomesPuppeteerScraper
    ↓
Raw_Scraped_Data (Google Sheet)
    ↓
Backup Files (JSON + Markdown)
```

### Extraction Flow

```
Raw_Scraped_Data (Google Sheet)
    ↓
run_extraction_step1.py
    ↓
RuleBasedExtractor
    ↓
ContentExtractor (per section)
    ↓
Content_Extraction (Google Sheet)
```

### Comparison Flow

```
Content_Extraction (Google Sheet)
    ↓
v0_property_comparison.py
    ↓
V0PropertyComparison
    ↓
V0_Comparison_Results (Google Sheet)
```

---

## Design Principles

### 1. Separation of Concerns

Each module has a single responsibility:
- Scrapers: Data fetching
- Extractors: Content extraction
- Comparators: Comparison logic
- Managers: External integrations

### 2. Modularity

Components are independent:
- Can run steps individually
- Easy to test
- Easy to extend

### 3. Error Handling

Comprehensive error handling:
- Try-except blocks
- Graceful degradation
- Detailed logging

### 4. Data Validation

Input validation:
- URL format checking
- JSON structure validation
- Missing data handling

---

## Key Design Decisions

### Why Rule-Based Extraction?

- **Accuracy:** Deterministic, no AI hallucinations
- **Speed:** Fast processing, no API calls
- **Reliability:** No external dependencies
- **Cost:** Free, no API costs

### Why Google Sheets?

- **Accessibility:** Easy to view and share
- **Visualization:** Built-in charts and formatting
- **Collaboration:** Multiple users can access
- **Integration:** Easy to export to other tools

### Why V0 (No Scoring)?

- **Simplicity:** Easy to understand
- **Focus:** Shows differences, not scores
- **Actionable:** Clear improvement areas
- **Maintainable:** Less complex logic

---

## Extension Points

### Adding New Scrapers

1. Create scraper class in `src/scrapers/`
2. Implement `scrape_url()` method
3. Return standard format
4. Add to `ScraperFactory`

### Adding New Sections

1. Add section name to extraction list
2. Implement extraction method in `ContentExtractor`
3. Add comparison logic in `V0PropertyComparison`
4. Update sheet headers

### Adding New Platforms

1. Create platform scraper
2. Add platform detection logic
3. Update extraction logic
4. Update comparison logic

---

## Testing Strategy

### Unit Tests (Future)

- Test individual components
- Mock external dependencies
- Test edge cases

### Integration Tests (Future)

- Test full pipeline
- Test with real data
- Test error scenarios

### Manual Testing

- Run full pipeline
- Verify data in sheets
- Check backup files

---

## Performance Considerations

### Optimization Strategies

1. **Batch Operations**
   - Batch Google Sheets writes
   - Reduce API calls

2. **Caching**
   - Cache scraped data
   - Avoid re-scraping

3. **Rate Limiting**
   - Delays between requests
   - Respect API limits

4. **Data Truncation**
   - Optimize large JSON
   - Keep essential data only

---

## Security Considerations

### Credentials

- Stored in `credentials.json` (gitignored)
- Never committed to repository
- Service account with minimal permissions

### Data Privacy

- No sensitive data logged
- Proper data handling
- Secure API calls

---

## Dependencies

### Core Dependencies

- `pandas` - Data manipulation
- `gspread` - Google Sheets API
- `google-auth` - Authentication
- `requests` - HTTP requests
- `selenium` - Browser automation (UHomes)

### Optional Dependencies

- `playwright` - Alternative browser automation
- `firecrawl-py` - Fallback scraper

---

## Code Quality

### Standards

- PEP 8 compliance
- Type hints (where applicable)
- Docstrings for all functions
- Clear variable names

### Documentation

- README with usage
- Docstrings in code
- Architecture documentation
- Flow documentation

---

## Future Enhancements

### Potential Additions

1. **Unit Tests**
   - Test individual components
   - Improve reliability

2. **Configuration File**
   - Move hardcoded values
   - Environment-specific configs

3. **Monitoring**
   - Metrics and alerting
   - Performance tracking

4. **API Endpoints**
   - REST API for integration
   - Webhook support

---

## Related Documentation

- [Scraping Guide](01_SCRAPING.md)
- [Extraction Guide](02_EXTRACTION.md)
- [V0 Comparison Guide](03_V0_COMPARISON.md)
- [Google Sheets Guide](04_GOOGLE_SHEETS.md)

---

**Last Updated:** December 2024
