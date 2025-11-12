# 🌐 Property Comparison Tool - Web UI

Beautiful, modern web interface for comparing property listings.

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
cd ui/
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python start_server.py
```

### 3. Open Browser

Navigate to: **http://localhost:8000**

---

## 🎯 Features

### ✅ File Upload Interface
- Drag & drop JSON files (Amber + Competitor)
- Instant validation
- Progress tracking

### ✅ Sample Data Testing
- One-click testing with built-in sample data
- No files needed

### ✅ Real-time Progress
- Live progress updates
- Stage-by-stage tracking
- Estimated time remaining

### ✅ Beautiful Results Display
- Summary statistics
- Interactive reports
- Download options (HTML, Markdown, JSON)

### ✅ Job Management
- Track multiple comparisons
- View recent jobs
- Delete old comparisons

---

## 📊 How It Works

```
User uploads files
       ↓
Frontend (HTML/CSS/JS)
       ↓
FastAPI Backend
       ↓
LangGraph Pipeline (4 AI Agents)
       ↓
Results displayed in UI
```

---

## 🏗️ Architecture

### Backend (FastAPI)

```
ui/backend/
└── app.py                 # FastAPI application
    ├── POST /api/compare  # Start comparison
    ├── GET /api/status    # Check progress
    ├── GET /api/results   # Get results
    └── GET /api/download  # Download reports
```

### Frontend

```
ui/frontend/
├── templates/
│   └── index.html        # Main UI
├── static/
│   ├── css/
│   │   └── styles.css    # Modern styling
│   └── js/
│       └── app.js        # Frontend logic
```

### Data Flow

```
uploads/                  # Uploaded JSON files
    ↓
Background processing     # LangGraph pipeline
    ↓
outputs/                  # Generated reports
    ├── {job_id}/
    │   ├── comparison_report.html
    │   ├── comparison_report.md
    │   ├── workflow_state.json
    │   └── summary.json
```

---

## 💻 API Endpoints

### `POST /api/compare`

Start a new comparison job.

**Request:**
```
Form Data:
- amber_file: JSON file
- competitor_file: JSON file
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Comparison started successfully"
}
```

### `GET /api/status/{job_id}`

Get job status and progress.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 45,
  "current_stage": "analyzing",
  "property_name": "iQ Sterling Court"
}
```

### `GET /api/results/{job_id}`

Get comparison results.

**Response:**
```json
{
  "job_id": "uuid",
  "summary": {
    "overall_similarity": 0.67,
    "amber_richness_score": 72,
    "total_insights": 8,
    "total_recommendations": 12
  },
  "markdown_report": "...",
  "html_url": "/api/download/uuid/html"
}
```

### `GET /api/download/{job_id}/{file_type}`

Download report file.

**file_type:** `html`, `markdown`, or `json`

---

## 🎨 UI Screenshots

### Upload Page
- Clean, modern design
- Drag & drop file inputs
- Sample data button
- Amber orange & blue theme

### Processing Page
- Real-time progress bar
- Stage indicators (5 stages)
- Animated loading states
- Estimated completion time

### Results Page
- Summary statistics (6 key metrics)
- Quick preview
- Download buttons (HTML, Markdown, JSON)
- View full report button

---

## 🔧 Configuration

### Server Settings

Edit `start_server.py`:
```python
uvicorn.run(
    "backend.app:app",
    host="0.0.0.0",      # Change to "127.0.0.1" for local only
    port=8000,            # Change port if needed
    reload=True           # Auto-reload on code changes
)
```

### Storage Locations

- **Uploads:** `ui/uploads/` - Uploaded JSON files
- **Outputs:** `ui/outputs/` - Generated reports

---

## 🚀 Usage

### For Team Members

1. Open http://localhost:8000
2. Upload Amber property JSON
3. Upload Competitor property JSON
4. Click "Start Comparison"
5. Wait 2-3 minutes
6. View/download reports

### For Development

```bash
# Start server with auto-reload
cd ui/
python start_server.py

# The server will automatically reload when you edit code
```

---

## 📝 Input JSON Format

```json
{
  "property_name": "Property Name",
  "url": "https://...",
  "provider": "Provider Name",
  "location": "City, Country",
  "extracted_content": {
    "text": "Full property page text...",
    "images": [{"url": "...", "alt": "..."}],
    "links": [{"url": "...", "text": "..."}],
    "meta_tags": {"title": "...", "description": "..."}
  }
}
```

---

## 🐛 Troubleshooting

### "Port already in use"

Change port in `start_server.py`:
```python
port=8001  # or any available port
```

### "Module not found"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "API key not found"

Create `.env` in project root:
```bash
cd ..
echo "OPENAI_API_KEY=sk-your-key" > .env
```

---

## 🎓 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) |
| **Frontend** | HTML5 + CSS3 + Vanilla JS |
| **AI Pipeline** | LangGraph + GPT-4 |
| **File Upload** | python-multipart |
| **Real-time Updates** | Polling (every 2s) |

---

## 🔮 Future Enhancements

- [ ] WebSocket for real-time updates (instead of polling)
- [ ] Batch processing (multiple properties)
- [ ] Historical comparisons view
- [ ] User authentication
- [ ] Database storage (instead of in-memory)
- [ ] Export to PDF
- [ ] Share reports via link

---

## 📞 Support

- **Setup Issues:** Check main project [SETUP_GUIDE.md](../SETUP_GUIDE.md)
- **API Errors:** Check logs in terminal where server is running
- **UI Issues:** Check browser console (F12)

---

**Access the UI:** http://localhost:8000 after starting the server!

**Built with FastAPI + Modern Web Technologies** 🚀


