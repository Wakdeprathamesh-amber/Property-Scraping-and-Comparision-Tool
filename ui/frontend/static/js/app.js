// Property Comparison Tool - Frontend Logic

let currentJobId = null;
let pollingInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadRecentJobs();
});

let currentMode = 'file'; // 'file', 'paste', or 'url'

function initializeEventListeners() {
    // Mode toggle buttons
    document.getElementById('fileModeBtn').addEventListener('click', () => switchMode('file'));
    document.getElementById('pasteModeBtn').addEventListener('click', () => switchMode('paste'));
    document.getElementById('urlModeBtn')?.addEventListener('click', () => switchMode('url'));
    
    // File input listeners
    document.getElementById('amberFile').addEventListener('change', (e) => {
        updateFileName('amberFileName', e.target.files[0]);
    });
    
    document.getElementById('competitorFile').addEventListener('change', (e) => {
        updateFileName('competitorFileName', e.target.files[0]);
    });
    
    // JSON paste validation and formatting
    document.getElementById('validateAmberJson').addEventListener('click', () => validateJson('amberJsonPaste', 'amberJsonStatus'));
    document.getElementById('validateCompetitorJson').addEventListener('click', () => validateJson('competitorJsonPaste', 'competitorJsonStatus'));
    
    document.getElementById('formatAmberJson').addEventListener('click', () => formatJson('amberJsonPaste'));
    document.getElementById('formatCompetitorJson').addEventListener('click', () => formatJson('competitorJsonPaste'));
    
    document.getElementById('clearAmberJson').addEventListener('click', () => clearJson('amberJsonPaste', 'amberJsonStatus'));
    document.getElementById('clearCompetitorJson').addEventListener('click', () => clearJson('competitorJsonPaste', 'competitorJsonStatus'));
    
    document.getElementById('loadSampleAmber').addEventListener('click', () => loadSampleData('amber'));
    document.getElementById('loadSampleCompetitor').addEventListener('click', () => loadSampleData('competitor'));
    
    // Auto-validate input on paste
    document.getElementById('amberJsonPaste').addEventListener('input', debounce(() => {
        const format = document.getElementById('inputFormat').value;
        validateInput('amberJsonPaste', 'amberJsonStatus', format, true);
    }, 500));
    
    document.getElementById('competitorJsonPaste').addEventListener('input', debounce(() => {
        const format = document.getElementById('inputFormat').value;
        validateInput('competitorJsonPaste', 'competitorJsonStatus', format, true);
    }, 500));
    
    // Update validation when format changes
    document.getElementById('inputFormat').addEventListener('change', () => {
        validateInput('amberJsonPaste', 'amberJsonStatus', document.getElementById('inputFormat').value, true);
        validateInput('competitorJsonPaste', 'competitorJsonStatus', document.getElementById('inputFormat').value, true);
    });
    
    // Form submit
    document.getElementById('comparisonForm').addEventListener('submit', handleFormSubmit);
    
    // Sample data button
    document.getElementById('useSampleBtn').addEventListener('click', useSampleData);
    
    // Results buttons
    document.getElementById('downloadCsvBtn')?.addEventListener('click', downloadCsv);
    document.getElementById('downloadJsonBtn')?.addEventListener('click', downloadJson);
    document.getElementById('newComparisonBtn')?.addEventListener('click', resetToUpload);
    document.getElementById('retryBtn')?.addEventListener('click', resetToUpload);
    document.getElementById('toggleFullscreen')?.addEventListener('click', toggleFullscreen);
}

function switchMode(mode) {
    currentMode = mode;
    
    // Update toggle buttons
    document.getElementById('fileModeBtn').classList.toggle('active', mode === 'file');
    document.getElementById('pasteModeBtn').classList.toggle('active', mode === 'paste');
    document.getElementById('urlModeBtn')?.classList.toggle('active', mode === 'url');
    
    // Show/hide modes
    document.getElementById('fileUploadMode').style.display = mode === 'file' ? 'flex' : 'none';
    document.getElementById('pasteJsonMode').style.display = mode === 'paste' ? 'flex' : 'none';
    
    const urlInputMode = document.getElementById('urlInputMode');
    if (urlInputMode) {
        urlInputMode.style.display = mode === 'url' ? 'flex' : 'none';
    }
    
    // Clear validation status
    clearJsonStatus(document.getElementById('amberJsonStatus'));
    clearJsonStatus(document.getElementById('competitorJsonStatus'));
    
    if (mode === 'url') {
        const amberUrlStatus = document.getElementById('amberUrlStatus');
        const competitorUrlStatus = document.getElementById('competitorUrlStatus');
        if (amberUrlStatus) clearJsonStatus(amberUrlStatus);
        if (competitorUrlStatus) clearJsonStatus(competitorUrlStatus);
    }
}

function isURL(text) {
    const trimmed = text.trim();
    return trimmed.startsWith('http://') || 
           trimmed.startsWith('https://') || 
           trimmed.startsWith('www.');
}

function detectFormat(text) {
    const trimmed = text.trim();
    
    // Check for URL FIRST
    if (isURL(trimmed)) {
        return 'url';
    }
    
    // Check for Markdown patterns FIRST (before JSON, to catch Markdown starting with [)
    // Markdown patterns that could be confused with JSON:
    // - Image syntax: ![alt](url) or [![alt](url)](link)
    // - Links: [text](url)
    // - Headers: #, ##, ###
    // - Lists: -, *, +
    const markdownPatterns = [
        /^\[!\[/,                    // Starts with [![ (Markdown image in link)
        /!\[[^\]]*\]\([^\)]+\)/,     // Image syntax ![alt](url)
        /\[[^\]]+\]\([^\)]+\)/,      // Link syntax [text](url)
        /^#{1,6}\s+/,                // Headers # ## ### etc
        /^[-*+]\s+/,                 // List items
        /^\d+\.\s+/,                 // Numbered lists
        /\*\*[^\*]+\*\*/,            // Bold **text**
        /__[^_]+__/,                 // Bold __text__
    ];
    
    // Count markdown patterns
    let markdownScore = 0;
    for (const pattern of markdownPatterns) {
        if (pattern.test(trimmed)) {
            markdownScore++;
        }
        // Also check in first 500 chars
        if (trimmed.length > 0 && pattern.test(trimmed.substring(0, 500))) {
            markdownScore++;
        }
    }
    
    // If strong markdown indicators, it's markdown
    if (markdownScore >= 2 || trimmed.startsWith('[![') || trimmed.startsWith('![')) {
        return 'markdown';
    }
    
    // Try JSON detection (only if not clearly markdown)
    // JSON should start with { or [ but check if it's valid JSON
    if (trimmed.startsWith('{')) {
        // JSON object - validate it
        try {
            const parsed = JSON.parse(trimmed);
            if (typeof parsed === 'object' && parsed !== null) {
                return 'json';
            }
        } catch (e) {
            // Not valid JSON - check if it has JSON-like structure
            if (trimmed.match(/^\s*\{[^}]*"[\w_]+"\s*:/)) {
                // Looks like JSON object syntax
                return 'json'; // Let backend try to parse
            }
        }
    } else if (trimmed.startsWith('[') && !trimmed.includes('](') && !trimmed.includes('![')) {
        // JSON array - but not if it has markdown link syntax
        try {
            const parsed = JSON.parse(trimmed);
            if (Array.isArray(parsed)) {
                return 'json';
            }
        } catch (e) {
            // Check if it looks like JSON array
            if (trimmed.match(/^\s*\[[^\]]*"[^"]*"/)) {
                return 'json';
            }
        }
    }
    
    // Additional markdown checks
    if (trimmed.includes('##') || trimmed.includes('###') || 
        trimmed.includes('**') || 
        (trimmed.includes('[') && trimmed.includes('](') && !trimmed.startsWith('{'))) {
        return 'markdown';
    }
    
    // Default to text
    return 'text';
}

function validateInput(textareaId, statusId, format = 'auto', silent = false) {
    const textarea = document.getElementById(textareaId);
    const status = document.getElementById(statusId);
    const inputText = textarea.value.trim();
    const badgeId = textareaId === 'amberJsonPaste' ? 'amberFormatBadge' : 'competitorFormatBadge';
    const formatBadge = document.getElementById(badgeId);
    
    if (!inputText) {
        if (!silent) {
            showJsonStatus(status, 'info', 'Please paste data (JSON, Text, or Markdown)');
        } else {
            clearJsonStatus(status);
        }
        formatBadge.textContent = '';
        formatBadge.className = 'format-badge';
        return false;
    }
    
    // Detect or use specified format
    const detectedFormat = format === 'auto' ? detectFormat(inputText) : format;
    
    // Update format badge
    formatBadge.textContent = `Format: ${detectedFormat}`;
    formatBadge.className = `format-badge detected ${detectedFormat}`;
    
    // URLs don't need validation - Firecrawl will handle them
    if (detectedFormat === 'url') {
        showJsonStatus(status, 'success', '🔥 Valid URL - will be scraped automatically');
        return true;
    }
    
    // Validate based on format
    if (detectedFormat === 'json') {
        try {
            const parsed = JSON.parse(inputText);
            
            // More lenient validation - check if it's a valid JSON object
            // Backend will handle mapping different field names
            if (typeof parsed !== 'object' || parsed === null) {
                showJsonStatus(status, 'error', 'JSON must be an object or array');
                return false;
            }
            
            // Try to detect property name from various possible fields
            const propertyName = parsed.property_name || parsed.name || parsed.data?.name || 
                               parsed.data?.property_name || parsed.title || 'Unknown';
            
            // If it's wrapped in a data structure, that's fine
            if (parsed.data && typeof parsed.data === 'object') {
                showJsonStatus(status, 'success', `✓ Valid JSON! Detected nested structure. Property: ${propertyName}`);
            } else {
                showJsonStatus(status, 'success', `✓ Valid JSON! Property: ${propertyName}`);
            }
            return true;
            
        } catch (error) {
            // If JSON parsing fails, it might be markdown or text that was mis-detected
            // Re-detect format and try again
            const reDetectedFormat = detectFormat(inputText);
            if (reDetectedFormat !== 'json') {
                // Format was mis-detected, update and validate with correct format
                formatBadge.textContent = `Format: ${reDetectedFormat}`;
                formatBadge.className = `format-badge detected ${reDetectedFormat}`;
                
                if (reDetectedFormat === 'markdown') {
                    if (inputText.length < 10) {
                        showJsonStatus(status, 'error', 'Input too short. Please provide more content.');
                        return false;
                    }
                    showJsonStatus(status, 'success', `✓ Valid Markdown! Content detected.`);
                    return true;
                } else {
                    // Text format
                    if (inputText.length < 10) {
                        showJsonStatus(status, 'error', 'Input too short. Please provide more content.');
                        return false;
                    }
                    showJsonStatus(status, 'success', `✓ Valid Text! Content detected.`);
                    return true;
                }
            }
            
            showJsonStatus(status, 'error', `✗ Invalid JSON: ${error.message}`);
            return false;
        }
    } else if (detectedFormat === 'markdown' || detectedFormat === 'text') {
        // For text/markdown - VERY PERMISSIVE!
        // Accept ANY text with at least 20 characters
        if (inputText.length < 20) {
            if (!silent) {
                showJsonStatus(status, 'error', 'Input too short. Please paste at least 20 characters.');
            }
            return false;
        }
        
        // Try to extract property name for display (optional)
        const nameMatch = inputText.match(/(?:property\s*name|name|title)[\s:]+([^\n]+)/i) || 
                         inputText.match(/^#+\s*(.+)$/m) ||
                         inputText.match(/^(.+?)(?:\n|$)/);
        
        const propertyName = nameMatch ? nameMatch[1].trim().substring(0, 50) : 'property';
        
        // Accept it!
        showJsonStatus(status, 'success', `✓ Valid ${detectedFormat}! ${inputText.length} chars - ${propertyName}`);
        return true;
    }
}

// Keep validateJson for backward compatibility, but redirect to validateInput
function validateJson(textareaId, statusId, silent = false) {
    const format = document.getElementById('inputFormat')?.value || 'auto';
    return validateInput(textareaId, statusId, format, silent);
}

function formatJson(textareaId) {
    const textarea = document.getElementById(textareaId);
    const jsonText = textarea.value.trim();
    
    if (!jsonText) {
        alert('No JSON to format');
        return;
    }
    
    try {
        const parsed = JSON.parse(jsonText);
        const formatted = JSON.stringify(parsed, null, 2);
        textarea.value = formatted;
        
        // Re-validate
        const statusId = textareaId === 'amberJsonPaste' ? 'amberJsonStatus' : 'competitorJsonStatus';
        validateJson(textareaId, statusId);
        
    } catch (error) {
        alert(`Invalid JSON: ${error.message}`);
    }
}

function clearJson(textareaId, statusId) {
    document.getElementById(textareaId).value = '';
    clearJsonStatus(document.getElementById(statusId));
}

function showJsonStatus(statusElement, type, message) {
    statusElement.textContent = message;
    statusElement.className = `json-status ${type}`;
}

function clearJsonStatus(statusElement) {
    statusElement.textContent = '';
    statusElement.className = 'json-status';
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function loadSampleData(type) {
    const sampleAmber = {
        "property_name": "iQ Sterling Court",
        "provider": "IQ Student Accommodation",
        "url": "https://amberstudent.com/properties/iq-sterling-court",
        "location": "Wembley, London HA9 0BU",
        "extracted_content": {
            "text": "iQ Sterling Court by IQ Student Accommodation\n\nLocated in Wembley, London HA9 0BU\nWeekly rent from £261 to £465\n660 units available\n\nAbout the Property:\niQ Sterling Court is a modern student accommodation located in Wembley, offering excellent transport links and contemporary living spaces.\n\nRooms:\n- Bronze Studio: £261/week\n- Silver Studio: £320/week\n- Gold Studio: £465/week\n\nAmenities:\n- Breakfast Bar\n- Courtyard Garden\n- Bicycle Storage\n- Social Spaces\n- Laundry Facility\n- High-Speed WiFi\n- All bills included\n\nPolicies:\n- No Visa No Pay\n- No Place No Pay\n- Replacement Tenant\n\nRating: Overall 4.2/5",
            "images": [{"url": "image1.jpg", "alt": "Bedroom"}],
            "links": [{"url": "/booking", "text": "Book Now"}],
            "meta_tags": {
                "title": "iQ Sterling Court | Student Accommodation",
                "description": "Book iQ Sterling Court in Wembley, London."
            }
        }
    };
    
    const sampleCompetitor = {
        "property_name": "iQ Sterling Court",
        "provider": "IQ",
        "url": "https://competitor.com/properties/iq-sterling-court",
        "location": "Wembley, London HA9 0BU",
        "extracted_content": {
            "text": "iQ Sterling Court by IQ\n\nSpecial Offer:\n💰 £500 Cashback on booking\n🎁 £250 Amazon Voucher\n🏷️ £880 total value offer!\n\nRooms Available:\n- Studios starting from £261/week\n- Ensuites available\n- Dual occupancy options\n\nAmenities:\n- Fully Furnished Rooms\n- Common Area\n- Table Tennis\n- Free WiFi\n\nTags:\n✨ Recently Refurbished Rooms\n🌍 International Guarantor Accepted\n👥 Free Dual Occupancy\n\nRating: 4.0/5",
            "images": [{"url": "competitor_image1.jpg", "alt": "Property"}],
            "links": [{"url": "/book", "text": "Book Now"}],
            "meta_tags": {
                "title": "iQ Sterling Court - Student Accommodation Wembley",
                "description": "iQ Sterling Court with special offers."
            }
        }
    };
    
    if (type === 'amber') {
        document.getElementById('amberJsonPaste').value = JSON.stringify(sampleAmber, null, 2);
        validateInput('amberJsonPaste', 'amberJsonStatus', 'json');
    } else {
        document.getElementById('competitorJsonPaste').value = JSON.stringify(sampleCompetitor, null, 2);
        validateInput('competitorJsonPaste', 'competitorJsonStatus', 'json');
    }
}

function updateFileName(elementId, file) {
    const fileNameElement = document.getElementById(elementId);
    if (file) {
        fileNameElement.textContent = file.name;
        fileNameElement.style.color = 'var(--success-color)';
    } else {
        fileNameElement.textContent = 'No file chosen';
        fileNameElement.style.color = 'var(--text-secondary)';
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    setButtonLoading('submitBtn', true);
    
    try {
        let response;
        
        if (currentMode === 'file') {
            // File upload mode
            const formData = new FormData();
            const amberFile = document.getElementById('amberFile').files[0];
            const competitorFile = document.getElementById('competitorFile').files[0];
            
            if (!amberFile || !competitorFile) {
                alert('⚠️ Please select both files');
                setButtonLoading('submitBtn', false);
                return;
            }
            
            formData.append('amber_file', amberFile);
            formData.append('competitor_file', competitorFile);
            
            response = await fetch('/api/compare', {
                method: 'POST',
                body: formData
            });
            
        } else if (currentMode === 'url') {
            // URL input mode - dedicated for Firecrawl scraping
            const amberUrl = document.getElementById('amberUrl').value.trim();
            const competitorUrl = document.getElementById('competitorUrl').value.trim();
            
            if (!amberUrl || !competitorUrl) {
                alert('⚠️ Please enter both URLs');
                setButtonLoading('submitBtn', false);
                return;
            }
            
            // Validate URLs
            if (!isURL(amberUrl)) {
                alert('⚠️ Amber URL is invalid. Please enter a valid URL starting with http:// or https://');
                setButtonLoading('submitBtn', false);
                return;
            }
            
            if (!isURL(competitorUrl)) {
                alert('⚠️ Competitor URL is invalid. Please enter a valid URL starting with http:// or https://');
                setButtonLoading('submitBtn', false);
                return;
            }
            
            // Show scraping status
            document.getElementById('uploadSection').style.display = 'none';
            const processingSection = document.getElementById('processingSection');
            if (processingSection) {
                processingSection.style.display = 'block';
            }
            
            const progressText = document.getElementById('progressText');
            if (progressText) {
                progressText.textContent = '🔥 Scraping websites with Firecrawl API...';
            }
            
            // Send URLs to backend (backend will detect and scrape)
            response = await fetch('/api/compare-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amber_data: amberUrl,
                    competitor_data: competitorUrl,
                    amber_format: 'auto',
                    competitor_format: 'auto'
                })
            });
            
        } else {
            // Paste JSON/Text/URL mode
            const amberJson = document.getElementById('amberJsonPaste').value.trim();
            const competitorJson = document.getElementById('competitorJsonPaste').value.trim();
            
            // Check if data is provided
            if (!amberJson || !competitorJson) {
                alert('⚠️ Please paste data or URLs in both fields');
                setButtonLoading('submitBtn', false);
                return;
            }
            
            // Get format (or auto-detect)
            const format = document.getElementById('inputFormat').value;
            
            // Validate input
            if (!validateInput('amberJsonPaste', 'amberJsonStatus', format)) {
                setButtonLoading('submitBtn', false);
                alert('⚠️ Amber data is invalid. Please fix errors before submitting.');
                return;
            }
            
            if (!validateInput('competitorJsonPaste', 'competitorJsonStatus', format)) {
                setButtonLoading('submitBtn', false);
                alert('⚠️ Competitor data is invalid. Please fix errors before submitting.');
                return;
            }
            
            // Prepare data - send raw text with format info
            const requestData = {
                amber_data: amberJson,
                competitor_data: competitorJson,
                amber_format: format === 'auto' ? detectFormat(amberJson) : format,
                competitor_format: format === 'auto' ? detectFormat(competitorJson) : format
            };
            
            response = await fetch('/api/compare-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start comparison');
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        // Switch to processing view
        showProcessingView();
        
        // Start polling for status
        startPolling(currentJobId);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
        setButtonLoading('submitBtn', false);
    }
}

async function useSampleData() {
    setButtonLoading('useSampleBtn', true);
    
    // Get full sample data from backend or use inline
    const sampleAmber = {
        "property_name": "iQ Sterling Court",
        "provider": "IQ Student Accommodation",
        "url": "https://amberstudent.com/properties/iq-sterling-court",
        "location": "Wembley, London HA9 0BU",
        "extracted_content": {
            "text": "iQ Sterling Court by IQ Student Accommodation\n\nLocated in Wembley, London HA9 0BU\nWeekly rent from £261 to £465\n660 units available\nDistance from city center: 7.6 miles\n\nAbout the Property:\niQ Sterling Court is a modern student accommodation located in Wembley, offering excellent transport links and contemporary living spaces. The property features a range of studio and ensuite rooms with all bills included.\n\nRooms:\n- Bronze Studio: £261/week - Private bathroom, study desk, storage, kitchenette\n- Silver Studio: £320/week - Larger space, private bathroom, full kitchen, study area\n- Gold Studio: £465/week - Premium room, spacious living area, modern furnishings\n- Bronze Ensuite: £285/week - Private bathroom, shared kitchen\n- Silver Ensuite: £310/week - Enhanced ensuite with more space\n\nAmenities:\nWe offer 9 key amenities:\n- Breakfast Bar\n- Courtyard Garden\n- Bicycle Storage\n- Social Spaces and Common Room\n- Laundry Facility\n- High-Speed WiFi\n- Heating included\n- Electricity included\n- Water included\n\nAll bills are included in the rent.\n\nPolicies:\n- No Visa No Pay: Get full refund if visa is rejected\n- No Place No Pay: Refund if you don't get university place\n- Replacement Tenant: Transfer booking if plans change\n- Deferring Studies: Move booking to next year\n\nPayments:\nPay by card or bank transfer. Choose from 1, 2, 3, or 4 instalment options.\n\nMedia:\n15+ high-quality images of rooms, kitchens, common areas\n5 video tours\n1 virtual 360° tour\n\nHighlights:\n- Close to University of Westminster\n- Close to University of West London\n- Affordable student-friendly pricing\n- Vibrant student community\n- Excellent transport links\n\nRating: Overall 4.2/5\n- Staff: 4.0/5\n- Social Life: 3.0/5\n- Location: 4.5/5\n- Facilities: 4.3/5",
            "images": [{"url": "image1.jpg", "alt": "Bedroom"}],
            "links": [{"url": "/booking", "text": "Book Now"}],
            "meta_tags": {
                "title": "iQ Sterling Court | Student Accommodation in Wembley | Amber",
                "description": "Book iQ Sterling Court student accommodation in Wembley, London."
            }
        }
    };
    
    const sampleCompetitor = {
        "property_name": "iQ Sterling Court",
        "provider": "IQ",
        "url": "https://competitor.com/properties/iq-sterling-court",
        "location": "Wembley, London HA9 0BU",
        "extracted_content": {
            "text": "iQ Sterling Court by IQ\n\nLocation: 6 Lakeside Way, Wembley, London HA9 0BU\nWeekly price from £261\nOverall rating: 4.0/5\n\nTags:\n✨ Recently Refurbished Rooms\n🌍 International Guarantor Accepted\n👥 Free Dual Occupancy\n📜 No Visa No Pay Policy\n✅ Instant Booking Available\n\nSpecial Offer:\n💰 £500 Cashback on booking\n🎁 £250 Amazon Voucher\n🏷️ £880 total value offer!\n\nRooms Available:\n- Studios starting from £261/week\n- Ensuites available\n- Dual occupancy options from £332/week\n\nAmenities:\n- Fully Furnished Rooms\n- Common Area\n- Table Tennis\n\nRoom Features:\nAll rooms include:\n- Private bathroom\n- Study desk and chair\n- Wardrobe storage\n- Free WiFi\n\nNearby:\n- Wembley Stadium (10 min walk)\n- Wembley Park Station (5 min walk)\n- Shopping center nearby\n- Restaurants and cafes\n\nWhy Choose iQ Sterling Court:\n✓ Recently refurbished modern rooms\n✓ Flexible dual occupancy options\n✓ No need for UK guarantor\n✓ Great transport connections\n✓ Vibrant Wembley location\n✓ Student-friendly community\n\nBook now to secure your cashback and voucher offer!",
            "images": [{"url": "competitor_image1.jpg", "alt": "Property"}],
            "links": [{"url": "/book", "text": "Book Now"}],
            "meta_tags": {
                "title": "iQ Sterling Court - Student Accommodation Wembley",
                "description": "iQ Sterling Court in Wembley. £500 cashback + £250 voucher."
            }
        }
    };
    
    try {
        // Send JSON directly
        const requestData = {
            amber_json: sampleAmber,
            competitor_json: sampleCompetitor
        };
        
        const response = await fetch('/api/compare-json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start comparison');
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        showProcessingView();
        startPolling(currentJobId);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
        setButtonLoading('useSampleBtn', false);
    }
}

function startPolling(jobId) {
    // Clear any existing interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Poll every 2 seconds
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const job = await response.json();
            
            updateProgress(job);
            
            if (job.status === 'completed') {
                clearInterval(pollingInterval);
                await showResults(jobId);
            } else if (job.status === 'failed') {
                clearInterval(pollingInterval);
                showError(job.error || 'Comparison failed');
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

function updateProgress(job) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    // Update progress bar
    let progress = job.progress || 0;
    progressFill.style.width = `${progress}%`;
    
    // Update text
    const stage = job.current_stage || 'processing';
    progressText.textContent = `${stage.replace(/_/g, ' ').toUpperCase()} (${progress}%)`;
    
    // Update stage indicators
    updateStageIndicators(stage);
}

function updateStageIndicators(currentStage) {
    const stages = ['validation', 'extraction', 'analysis', 'comparison', 'reporting'];
    const stageMapping = {
        'input_validation': 0,
        'quality_assessment': 0,
        'extract': 1,
        'validate_sections': 1,
        'analyze': 2,
        'compare': 3,
        'comparison': 3,
        'insights': 4,
        'recommendations': 4,
        'reporting': 4,
        'reports': 4
    };
    
    const currentIndex = stageMapping[currentStage] ?? -1;
    
    document.querySelectorAll('.stage-item').forEach((item, index) => {
        const stage = item.getAttribute('data-stage');
        const stageIndex = stages.indexOf(stage);
        
        if (stageIndex < currentIndex) {
            item.classList.add('completed');
            item.classList.remove('active');
        } else if (stageIndex === currentIndex) {
            item.classList.add('active');
            item.classList.remove('completed');
        } else {
            item.classList.remove('active', 'completed');
        }
    });
}

async function showResults(jobId) {
    try {
        const response = await fetch(`/api/results/${jobId}`);
        const data = await response.json();
        
        const summary = data.summary;
        
        // Update stats
        document.getElementById('statSimilarity').textContent = 
            `${(summary.overall_similarity * 100).toFixed(1)}%`;
        document.getElementById('statAmberScore').textContent = 
            `${summary.amber_richness_score.toFixed(0)}/100`;
        document.getElementById('statCompetitorScore').textContent = 
            `${summary.competitor_richness_score.toFixed(0)}/100`;
        document.getElementById('statInsights').textContent = 
            summary.total_insights;
        document.getElementById('statRecommendations').textContent = 
            summary.total_recommendations;
        document.getElementById('statTime').textContent = 
            `${summary.processing_time_seconds.toFixed(0)}s`;
        
        // Show HTML report preview inline
        if (data.html_report) {
            // Create an iframe to display the HTML report safely
            const previewContent = document.getElementById('previewContent');
            previewContent.innerHTML = '';
            
            // Create iframe for HTML preview
            const iframe = document.createElement('iframe');
            iframe.id = 'reportIframe';
            iframe.style.width = '100%';
            iframe.style.height = '800px';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '8px';
            iframe.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            iframe.srcdoc = data.html_report;
            previewContent.appendChild(iframe);
        } else {
            // Fallback to markdown preview if HTML not available
            const preview = data.markdown_report.split('\n').slice(0, 30).join('\n');
            document.getElementById('previewContent').innerHTML = 
                `<pre style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem;">${escapeHtml(preview)}\n\n... (generating HTML report)</pre>`;
        }
        
        // Show results section
        showView('resultsSection');
        
    } catch (error) {
        console.error('Error loading results:', error);
        showError('Failed to load results');
    }
}

function downloadCsv() {
    if (currentJobId) {
        window.location.href = `/api/download/${currentJobId}/csv`;
    }
}

function downloadJson() {
    if (currentJobId) {
        window.location.href = `/api/download/${currentJobId}/json`;
    }
}

function toggleFullscreen() {
    const previewContent = document.getElementById('previewContent');
    const iframe = document.getElementById('reportIframe');
    
    if (!document.fullscreenElement) {
        // Enter fullscreen
        if (previewContent.requestFullscreen) {
            previewContent.requestFullscreen();
        } else if (previewContent.webkitRequestFullscreen) {
            previewContent.webkitRequestFullscreen();
        } else if (previewContent.msRequestFullscreen) {
            previewContent.msRequestFullscreen();
        }
        
        if (iframe) {
            iframe.style.height = '100vh';
        }
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        
        if (iframe) {
            iframe.style.height = '800px';
        }
    }
}

function showView(sectionId) {
    // Hide all sections
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    
    // Show requested section
    document.getElementById(sectionId).style.display = 'block';
    document.getElementById(sectionId).classList.add('fadeIn');
}

function showProcessingView() {
    showView('processingSection');
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    showView('errorSection');
}

function resetToUpload() {
    // Clear form
    document.getElementById('comparisonForm').reset();
    document.getElementById('amberFileName').textContent = 'No file chosen';
    document.getElementById('competitorFileName').textContent = 'No file chosen';
    
    // Clear JSON textareas
    document.getElementById('amberJsonPaste').value = '';
    document.getElementById('competitorJsonPaste').value = '';
    clearJsonStatus(document.getElementById('amberJsonStatus'));
    clearJsonStatus(document.getElementById('competitorJsonStatus'));
    
    // Reset mode to file
    switchMode('file');
    
    // Reset states
    currentJobId = null;
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    
    // Show upload section
    showView('uploadSection');
}

function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');
    
    if (isLoading) {
        btnText.style.display = 'none';
        if (btnLoader) {
            btnLoader.style.display = 'flex';
        }
        button.disabled = true;
    } else {
        btnText.style.display = 'block';
        if (btnLoader) {
            btnLoader.style.display = 'none';
        }
        button.disabled = false;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadRecentJobs() {
    // Optional: Load recent jobs on page load
    try {
        const response = await fetch('/api/jobs');
        const data = await response.json();
        // Could display recent jobs in sidebar
        console.log('Recent jobs:', data.jobs.length);
    } catch (error) {
        console.log('No recent jobs found');
    }
}

