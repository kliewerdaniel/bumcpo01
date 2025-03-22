"""
Web Interface module for Browser Automation for Research.

This module provides a web interface using FastAPI for interacting with the research system,
allowing users to submit queries and view results through a browser.
"""
import logging
import asyncio
import os
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Pydantic models for API
class ResearchQuery(BaseModel):
    """Research query model."""
    query: str
    max_results: Optional[int] = 10


class ResearchProgress(BaseModel):
    """Research progress model."""
    query_id: str
    status: str
    progress: int
    total_steps: int
    current_step: Optional[str] = None
    message: Optional[str] = None


class ResearchResult(BaseModel):
    """Research result model."""
    query_id: str
    query: str
    report: str
    created_at: float
    file_path: Optional[str] = None


class WebInterface:
    """
    Web interface for the research system using FastAPI.
    
    This class provides a web-based interface for submitting research queries
    and viewing results through a browser.
    """
    
    def __init__(self, orchestrator: Dict[str, Any], config: Dict[str, Any]):
        """
        Initialize the web interface.
        
        Args:
            orchestrator: Dictionary containing orchestration components
            config: Web interface configuration
        """
        self.planner = orchestrator["planner"]
        self.executor = orchestrator["executor"]
        self.generator = orchestrator["generator"]
        
        self.config = config
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 8080)
        self.debug = config.get("debug", False)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Browser Automation for Research",
            description="Web interface for the AI-powered research assistant",
            version="1.0.0"
        )
        
        # Create dirs for static files and templates
        self.static_dir = Path("static")
        self.templates_dir = Path("templates")
        self.reports_dir = Path("reports")
        
        # Ensure directories exist
        self.static_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Create simple HTML template for the interface
        self._create_templates()
        
        # Create static files
        self._create_static_files()
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Templates
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        # Active research tasks
        self.active_tasks = {}  # Maps query_id to task info
        self.results = {}  # Maps query_id to results
        
        # Register routes
        self._register_routes()
    
    def _create_templates(self):
        """Create the HTML templates for the web interface."""
        # Create index.html template
        index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Automation for Research</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Browser Automation for Research</h1>
            <p>Enter a research query to get comprehensive information from multiple sources.</p>
        </header>
        
        <main>
            <section class="query-section">
                <div class="query-form">
                    <textarea id="query-input" placeholder="Enter your research question here..."></textarea>
                    <div class="form-controls">
                        <label for="max-results">Maximum results per source: 
                            <input type="number" id="max-results" min="1" max="20" value="5">
                        </label>
                        <button id="submit-query">Research</button>
                    </div>
                </div>
            </section>
            
            <section id="progress-section" class="hidden">
                <h2>Research in Progress</h2>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div id="progress-fill" class="progress-fill"></div>
                    </div>
                    <div id="progress-text">0%</div>
                </div>
                <div id="current-step"></div>
            </section>
            
            <section id="results-section" class="hidden">
                <h2>Research Results</h2>
                <div class="results-actions">
                    <button id="download-report">Download Report</button>
                    <button id="new-query">New Research</button>
                </div>
                <div id="report-content" class="markdown-body"></div>
            </section>
            
            <section id="history-section">
                <h2>Recent Research</h2>
                <div id="history-list">
                    <!-- History items will be added here -->
                    <div class="no-history">No recent research available.</div>
                </div>
            </section>
        </main>
        
        <footer>
            <p>Browser Automation for Research - AI-powered research assistant</p>
        </footer>
    </div>
    
    <script src="/static/main.js"></script>
</body>
</html>
        """
        
        with open(self.templates_dir / "index.html", "w") as f:
            f.write(index_html)
    
    def _create_static_files(self):
        """Create static files for the web interface."""
        # Create styles.css
        styles_css = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 40px;
    padding: 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

header h1 {
    margin-bottom: 10px;
    color: #2c3e50;
}

section {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 30px;
}

.query-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

textarea {
    width: 100%;
    min-height: 120px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    resize: vertical;
}

.form-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #45a049;
}

input[type="number"] {
    width: 60px;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.progress-container {
    margin: 20px 0;
}

.progress-bar {
    height: 20px;
    background-color: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background-color: #4CAF50;
    width: 0%;
    transition: width 0.3s;
}

#current-step {
    font-style: italic;
    color: #666;
}

.markdown-body {
    padding: 20px;
    line-height: 1.6;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
}

.markdown-body h1 {
    font-size: 2em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
}

.markdown-body h2 {
    font-size: 1.5em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
}

.markdown-body p {
    margin-top: 0;
    margin-bottom: 16px;
}

.markdown-body ul, .markdown-body ol {
    padding-left: 2em;
    margin-bottom: 16px;
}

.results-actions {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
}

.history-item {
    padding: 15px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: background-color 0.2s;
}

.history-item:hover {
    background-color: #f5f5f5;
}

.history-item h3 {
    font-size: 18px;
    margin-bottom: 5px;
}

.history-item p {
    color: #666;
    font-size: 14px;
}

.no-history {
    text-align: center;
    color: #888;
    padding: 20px;
}

.hidden {
    display: none;
}

footer {
    text-align: center;
    margin-top: 30px;
    padding: 20px;
    color: #777;
    font-size: 14px;
}

@media (max-width: 768px) {
    .form-controls {
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
    }
    
    .results-actions {
        flex-direction: column;
        gap: 10px;
    }
    
    button {
        width: 100%;
    }
}
        """
        
        with open(self.static_dir / "styles.css", "w") as f:
            f.write(styles_css)
        
        # Create main.js
        main_js = """
document.addEventListener('DOMContentLoaded', function() {
    const queryInput = document.getElementById('query-input');
    const maxResultsInput = document.getElementById('max-results');
    const submitButton = document.getElementById('submit-query');
    const progressSection = document.getElementById('progress-section');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const currentStepEl = document.getElementById('current-step');
    const resultsSection = document.getElementById('results-section');
    const reportContent = document.getElementById('report-content');
    const downloadReportBtn = document.getElementById('download-report');
    const newQueryBtn = document.getElementById('new-query');
    const historyList = document.getElementById('history-list');
    
    let activeQueryId = null;
    let websocket = null;
    
    // Initialize the page
    loadResearchHistory();
    
    // Add event listeners
    submitButton.addEventListener('click', startResearch);
    downloadReportBtn.addEventListener('click', downloadReport);
    newQueryBtn.addEventListener('click', resetInterface);
    
    // Function to start a new research
    function startResearch() {
        const query = queryInput.value.trim();
        const maxResults = parseInt(maxResultsInput.value, 10);
        
        if (!query) {
            alert('Please enter a research query');
            return;
        }
        
        // Show progress section
        progressSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        submitButton.disabled = true;
        
        // Reset progress indicators
        progressFill.style.width = '0%';
        progressText.textContent = '0%';
        currentStepEl.textContent = 'Analyzing query...';
        
        // Start the research
        fetch('/api/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                max_results: maxResults
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            activeQueryId = data.query_id;
            
            // Connect to WebSocket for progress updates
            connectWebSocket(activeQueryId);
        })
        .catch(error => {
            alert('Error starting research: ' + error.message);
            submitButton.disabled = false;
            progressSection.classList.add('hidden');
        });
    }
    
    // Function to connect to WebSocket for progress updates
    function connectWebSocket(queryId) {
        // Close existing connection if any
        if (websocket) {
            websocket.close();
        }
        
        // Create new WebSocket connection
        websocket = new WebSocket(`ws://${window.location.host}/ws/research/${queryId}`);
        
        websocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Update progress
            const progress = Math.round((data.progress / data.total_steps) * 100);
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${progress}%`;
            
            if (data.current_step) {
                currentStepEl.textContent = data.current_step;
            }
            
            // Check if research is complete
            if (data.status === 'complete') {
                // Load the results
                loadResearchResult(queryId);
                
                // Close WebSocket
                websocket.close();
                websocket = null;
            }
        };
        
        websocket.onerror = function(event) {
            console.error('WebSocket error:', event);
            alert('Error connecting to server for progress updates');
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket connection closed');
        };
    }
    
    // Function to load research result
    function loadResearchResult(queryId) {
        fetch(`/api/research/${queryId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Display the results
                reportContent.innerHTML = renderMarkdown(data.report);
                
                // Show results section, hide progress section
                progressSection.classList.add('hidden');
                resultsSection.classList.remove('hidden');
                submitButton.disabled = false;
                
                // Update research history
                loadResearchHistory();
            })
            .catch(error => {
                alert('Error loading research results: ' + error.message);
                submitButton.disabled = false;
                progressSection.classList.add('hidden');
            });
    }
    
    // Function to download the report
    function downloadReport() {
        if (!activeQueryId) return;
        
        window.location.href = `/api/research/${activeQueryId}/download`;
    }
    
    // Function to reset the interface for a new query
    function resetInterface() {
        queryInput.value = '';
        resultsSection.classList.add('hidden');
        activeQueryId = null;
    }
    
    // Function to load research history
    function loadResearchHistory() {
        fetch('/api/history')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Clear current history
                historyList.innerHTML = '';
                
                if (data.history.length === 0) {
                    historyList.innerHTML = '<div class="no-history">No recent research available.</div>';
                    return;
                }
                
                // Add history items
                data.history.forEach(item => {
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    historyItem.dataset.queryId = item.query_id;
                    
                    // Format date
                    const date = new Date(item.created_at * 1000);
                    const formattedDate = date.toLocaleString();
                    
                    historyItem.innerHTML = `
                        <h3>${item.query}</h3>
                        <p>Completed: ${formattedDate}</p>
                    `;
                    
                    historyItem.addEventListener('click', function() {
                        activeQueryId = item.query_id;
                        loadResearchResult(item.query_id);
                    });
                    
                    historyList.appendChild(historyItem);
                });
            })
            .catch(error => {
                console.error('Error loading research history:', error);
                historyList.innerHTML = '<div class="no-history">Error loading research history</div>';
            });
    }
    
    // Function to render Markdown
    function renderMarkdown(markdown) {
        // Very simple Markdown rendering
        return markdown
            // Headers
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Lists
            .replace(/^\- (.*$)/gm, '<li>$1</li>')
            // Links
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Paragraphs
            .replace(/\n\n/g, '</p><p>')
            // Wrap in paragraphs
            .replace(/^(.+?)$/gm, '<p>$1</p>');
    }
});
        """
        
        with open(self.static_dir / "main.js", "w") as f:
            f.write(main_js)
    
    def _register_routes(self):
        """Register FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """Render the index page."""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.post("/api/research", response_model=Dict[str, Any])
        async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
            """Start a new research task."""
            # Generate query_id
            query_id = str(uuid.uuid4())
            
            # Store task info
            self.active_tasks[query_id] = {
                "query": query.query,
                "max_results": query.max_results,
                "status": "pending",
                "progress": 0,
                "total_steps": 0,
                "started_at": time.time()
            }
            
            # Start the research task in background
            background_tasks.add_task(self._conduct_research, query_id, query.query, query.max_results)
            
            return {"query_id": query_id}
        
        @self.app.get("/api/research/{query_id}", response_model=Dict[str, Any])
        async def get_research_result(query_id: str):
            """Get research results for a given query ID."""
            if query_id in self.results:
                return self.results[query_id]
            elif query_id in self.active_tasks:
                return {
                    "query_id": query_id,
                    "status": self.active_tasks[query_id]["status"],
                    "progress": self.active_tasks[query_id]["progress"],
                    "total_steps": self.active_tasks[query_id]["total_steps"]
                }
            else:
                raise HTTPException(status_code=404, detail="Research not found")
        
        @self.app.get("/api/research/{query_id}/download")
        async def download_report(query_id: str):
            """Download research report as a Markdown file."""
            if query_id not in self.results:
                raise HTTPException(status_code=404, detail="Research not found")
            
            result = self.results[query_id]
            
            # Create filename from query
            safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in result["query"])
            safe_query = safe_query[:50]  # Limit length
            filename = f"research_{safe_query}_{int(result['created_at'])}.md"
            
            # Return file response
            from fastapi.responses import FileResponse
            return FileResponse(
                path=result["file_path"],
                filename=filename,
                media_type="text/markdown"
            )
        
        @self.app.get("/api/history", response_model=Dict[str, Any])
        async def get_research_history():
            """Get research history."""
            # Convert results to list and sort by creation time (newest first)
            history = list(self.results.values())
            history.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Return only essential info
            return {
                "history": [
                    {
                        "query_id": item["query_id"],
                        "query": item["query"],
                        "created_at": item["created_at"]
                    } for item in history
                ]
            }
        
        @self.app.websocket("/ws/research/{query_id}")
        async def websocket_research_progress(websocket: WebSocket, query_id: str):
            """WebSocket endpoint for research progress updates."""
            await websocket.accept()
            
            try:
                # Check if query exists
                if query_id not in self.active_tasks and query_id not in self.results:
                    await websocket.close(code=1000, reason="Research not found")
                    return
                
                # If research is already complete, send the final update
                if query_id in self.results:
                    await websocket.send_json({
                        "query_id": query_id,
                        "status": "complete",
                        "progress": 100,
                        "total_steps": 100
                    })
                    await websocket.close()
                    return
                
                # Send initial progress
                await websocket.send_json({
                    "query_id": query_id,
                    "status": self.active_tasks[query_id]["status"],
                    "progress": self.active_tasks[query_id]["progress"],
                    "total_steps": self.active_tasks[query_id]["total_steps"],
                    "current_step": self.active_tasks[query_id].get("current_step")
                })
                
                # Wait for updates
                while query_id in self.active_tasks:
                    # Send progress update
                    await websocket.send_json({
                        "query_id": query_id,
                        "status": self.active_tasks[query_id]["status"],
                        "progress": self.active_tasks[query_id]["progress"],
                        "total_steps": self.active_tasks[query_id]["total_steps"],
                        "current_step": self.active_tasks[query_id].get("current_step")
                    })
                    
                    # Check if research is complete
                    if self.active_tasks[query_id]["status"] == "complete":
                        await websocket.close()
                        break
                    
                    # Wait a bit before sending next update
                    await asyncio.sleep(1)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for query {query_id}")
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")
                await websocket.close(code=1011, reason="Server error")
    
    async def _conduct_research(self, query_id: str, query: str, max_results: int):
        """
        Conduct research based on the query.
        
        Args:
            query_id: Unique ID for this research
            query: The research query
            max_results: Maximum results per source
        """
        try:
            # Get task info
            task_info = self.active_tasks[query_id]
            task_info["status"] = "analyzing"
            task_info["current_step"] = "Analyzing query and planning research"
            
            # Create research plan
            research_plan = await self.planner.create_research_plan(query)
            
            # Update task info with total steps
            task_info["total_steps"] = len(research_plan["steps"])
            task_info["status"] = "researching"
            
            # Setup progress tracking
            def progress_callback(step, result):
                task_info["progress"] += 1
                task_info["current_step"] = f"Step {task_info['progress']}: {step.get('type', 'Unknown')}"
            
            # Execute research plan
            self.executor.on_step_complete = progress_callback
            research_results = await self.executor.execute_research_plan(research_plan)
            
            # Update task status
            task_info["status"] = "generating_report"
            task_info["current_step"] = "Generating final research report"
            
            # Generate report
            report = await self.generator.generate_report(research_results)
            
            # Save report to file
            safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
            safe_query = safe_query[:50]  # Limit length
            filename = f"research_{safe_query}_{int(time.time())}.md"
            file_path = self.reports_dir / filename
            
            with open(file_path, "w") as f:
                f.write(report)
            
            # Store result
            self.results[query_id] = {
                "query_id": query_id,
                "query": query,
                "report": report,
                "created_at": time.time(),
                "file_path": str(file_path)
            }
            
            # Mark task as complete
            task_info["status"] = "complete"
            task_info["progress"] = task_info["total_steps"]
            
            # Remove from active tasks after a delay (to allow final status to be sent)
            await asyncio.sleep(5)
            if query_id in self.active_tasks:
                del self.active_tasks[query_id]
            
        except Exception as e:
            logger.error(f"Error conducting research: {e}")
            
            # Update task status
            if query_id in self.active_tasks:
                self.active_tasks[query_id]["status"] = "error"
                self.active_tasks[query_id]["error"] = str(e)
                
                # Remove from active tasks after a delay
                await asyncio.sleep(5)
                if query_id in self.active_tasks:
                    del self.active_tasks[query_id]
    
    async def start(self):
        """Start the web interface."""
        import uvicorn
        
        # Create resources (templates, static files)
        self._create_templates()
        self._create_static_files()
        
        # Run with uvicorn
        config = uvicorn.Config(app=self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
    
    async def stop(self):
        """Stop the web interface."""
        # Nothing specific to do here for FastAPI
        pass
