# 🏠 Property Page Comparator

An AI-powered tool to compare property listings between Amber and competitors, providing deep content analysis and actionable insights.

## 📖 Overview

This tool performs intelligent comparison of property pages through a **4-agent AI pipeline**:

1. **Agent 1**: Extracts and identifies sections from raw property data
2. **Agent 2**: Deeply analyzes each section for depth, quality, and richness
3. **Agent 3**: Compares properties and generates insights
4. **Agent 4**: Creates beautiful, actionable reports

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI or Anthropic API key

### Installation

```bash
# Clone or navigate to project directory
cd "Property Diff scraper"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API key
```

### Usage

#### Option 1: Using Sample Data (for testing)

```bash
python main.py --sample
```

#### Option 2: Using Your Own Data

```bash
python main.py \
  --amber-data path/to/amber_property.json \
  --competitor-data path/to/competitor_property.json \
  --output-dir outputs/my-comparison
```

#### Option 3: Interactive Mode

```bash
python main.py --interactive
```

## 📁 Input Data Format

The tool expects JSON files with the following structure:

```json
{
  "property_name": "iQ Sterling Court",
  "provider": "IQ Student Accommodation",
  "url": "https://...",
  "location": "London, UK",
  "raw_html": "<html>...</html>",
  "extracted_content": {
    "text": "Full visible text from page...",
    "sections": [
      {
        "heading": "About",
        "content": "Description text..."
      }
    ],
    "images": [
      {"url": "...", "alt": "..."}
    ],
    "links": [...],
    "meta_tags": {...}
  }
}
```

See `test_data/sample_amber.json` for a complete example.

## 📊 Output

The tool generates:

- **JSON**: Structured comparison data (`comparison_data.json`)
- **Markdown**: Human-readable report (`comparison_report.md`)
- **HTML**: Styled web report (`comparison_report.html`)

## 🏗️ Architecture

```
Input JSON Data
    ↓
Agent 1: Section Extractor
    ↓
Agent 2: Deep Analyzer
    ↓
Agent 3: Comparative Evaluator
    ↓
Agent 4: Report Generator
    ↓
Output Reports
```

## 📚 Documentation

- [Project Specification](PROJECT_SPECIFICATION.md) - Complete technical documentation
- [Agent Architecture](docs/agents.md) - Detailed agent descriptions (coming soon)

## 🛠️ Development

```bash
# Run tests
pytest tests/

# Format code
black src/

# Type checking
mypy src/
```

## 📝 License

Internal tool for Amber Student

## 🤝 Contributing

Contact the Product/Engineering team for access and contribution guidelines.


