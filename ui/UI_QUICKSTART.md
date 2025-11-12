# 🚀 UI Quick Start Guide

## Launch in 2 Minutes

### Step 1: Install UI Dependencies

```bash
cd ui/
../venv/bin/pip install -r requirements.txt
```

### Step 2: Start the Server

```bash
cd ui/
../venv/bin/python start_server.py
```

You'll see:
```
🏠 Property Comparison Tool - Web UI
📡 Starting server...
🌐 Access the UI at: http://localhost:8000
```

### Step 3: Open Browser

Go to: **http://localhost:8000**

---

## 🎯 How to Use

### Option 1: Upload Your Files

1. **Select Amber JSON file** - Click "Amber Property Data" button
2. **Select Competitor JSON file** - Click "Competitor Property Data" button
3. **Click "Start Comparison"**
4. **Wait 2-3 minutes** - Watch progress in real-time
5. **View Results** - Click "View HTML Report"

### Option 2: Use Sample Data

1. Click **"📝 Use Sample Data"** button
2. System automatically uses built-in sample data
3. Watch processing happen
4. View results

---

## 🌐 UI Features

### Upload Page
- ✅ Clean, modern interface
- ✅ File validation
- ✅ Instant feedback
- ✅ Sample data option

### Processing Page
- ✅ Real-time progress bar (0-100%)
- ✅ Stage indicators (5 stages):
  - Input Validation
  - Section Extraction
  - Deep Analysis
  - Comparison
  - Report Generation
- ✅ Estimated time (2-3 minutes)
- ✅ Animated loading states

### Results Page
- ✅ 6 key metrics displayed:
  - Content Similarity %
  - Amber Richness Score
  - Competitor Richness Score
  - Total Insights
  - Total Recommendations
  - Processing Time
- ✅ Quick preview of report
- ✅ Download buttons:
  - 🌐 View HTML Report (opens in new tab)
  - 📄 Download Markdown
  - 📊 Download JSON
- ✅ Start new comparison button

---

## 📊 Screenshots

### 1. Upload Interface

```
┌─────────────────────────────────────────────┐
│  🏠 Property Comparison Tool                │
│     AI-powered property listing analysis    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 📊 Compare Properties                       │
│                                              │
│ Upload property data from Amber and a       │
│ competitor to generate comprehensive        │
│ comparison reports...                       │
│                                              │
│ 🟠 Amber Property Data (JSON)               │
│ [ Choose File ] sample_amber.json           │
│                                              │
│ 🔵 Competitor Property Data (JSON)          │
│ [ Choose File ] sample_competitor.json      │
│                                              │
│        [ 🚀 Start Comparison ]              │
│                                              │
│ ───────────────────────────────────         │
│        [ 📝 Use Sample Data ]               │
└─────────────────────────────────────────────┘
```

### 2. Processing View

```
┌─────────────────────────────────────────────┐
│ ⚙️ Processing Comparison                    │
│                                              │
│ [██████████████────────] 65%                │
│ ANALYZING SECTIONS                          │
│                                              │
│ ✅ Input Validation    ⏳ Comparison        │
│ ✅ Section Extraction  ⏳ Report Generation │
│ 🔄 Deep Analysis                            │
│                                              │
│ Estimated time: 2-3 minutes                 │
└─────────────────────────────────────────────┘
```

### 3. Results View

```
┌─────────────────────────────────────────────┐
│ ✅ Comparison Complete!                     │
│                                              │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│ │ 67%  │ │ 72   │ │ 58   │ │  8   │       │
│ │Simil.│ │Amber │ │Comp. │ │Insigh│       │
│ └──────┘ └──────┘ └──────┘ └──────┘       │
│                                              │
│ [ 🌐 View HTML Report ]                     │
│ [ 📄 Download Markdown ] [ 📊 Download JSON]│
│                                              │
│ 📋 Quick Preview:                           │
│ # Property Comparison Report...             │
│ ...                                          │
└─────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Change Port

Edit `start_server.py`:
```python
port=8000  # Change to any available port
```

### Enable CORS

Edit `backend/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    ...
)
```

---

## 📁 File Structure

```
ui/
├── start_server.py           # Server startup script
├── requirements.txt          # UI dependencies
├── README.md                 # This file
│
├── backend/
│   └── app.py               # FastAPI application
│
├── frontend/
│   ├── templates/
│   │   └── index.html       # Main UI page
│   └── static/
│       ├── css/
│       │   └── styles.css   # Styling
│       └── js/
│           └── app.js       # Frontend logic
│
├── uploads/                  # Uploaded files (auto-created)
└── outputs/                  # Generated reports (auto-created)
```

---

## 🐛 Troubleshooting

### Server won't start

**Check if port is in use:**
```bash
lsof -i :8000
```

**Kill process:**
```bash
kill -9 <PID>
```

### "Module not found"

**Install dependencies:**
```bash
cd ui/
pip install -r requirements.txt
```

### "Can't connect to server"

**Check server is running:**
```bash
# Should see "Application startup complete"
# Check http://localhost:8000/health
```

### File upload fails

**Check file size:**
- JSON files should be < 10MB
- Check file is valid JSON
- Check required fields exist

---

## 💡 Tips

### Development

```bash
# Run with auto-reload (changes reflect automatically)
python start_server.py

# Check logs
# Server logs appear in terminal
```

### Production

```bash
# Run without reload
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Or use process manager like PM2, systemd
```

### Testing

```bash
# Test with sample data
# 1. Start server
# 2. Click "Use Sample Data"
# 3. Verify results

# Test with your files
# 1. Prepare JSON files
# 2. Upload via UI
# 3. Check results
```

---

## 🎓 For Developers

### Add New Endpoint

```python
# backend/app.py

@app.get("/api/custom")
async def custom_endpoint():
    return {"message": "Custom endpoint"}
```

### Modify UI

```html
<!-- frontend/templates/index.html -->
<!-- Add new sections here -->
```

```css
/* frontend/static/css/styles.css */
/* Add custom styling */
```

```javascript
// frontend/static/js/app.js
// Add custom logic
```

---

## 📊 Performance

- **Upload:** < 1 second
- **Processing:** 2-3 minutes (depends on content length)
- **Results Display:** < 1 second

---

## 🔒 Security Notes

### Current (Development)

- ⚠️ CORS enabled for all origins
- ⚠️ No authentication
- ⚠️ No rate limiting
- ⚠️ Files stored locally

### For Production

- ✅ Add authentication (OAuth/JWT)
- ✅ Restrict CORS origins
- ✅ Add rate limiting
- ✅ Use cloud storage
- ✅ Add HTTPS

---

## 🎉 You're Ready!

```bash
cd ui/
python start_server.py
```

Then open: **http://localhost:8000**

---

**Enjoy the beautiful UI!** 🏠✨


