"""
Master Automation Web Control Center
Zero-dependency, standalone HTTP server running on http://localhost:8888.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from orchestrator import MasterOrchestrator, load_config
from stats_collector import get_all_stats
from scheduler_manager import get_task_status, register_windows_task, remove_windows_task
from export_master_csv import export_all

BASE_DIR = Path(__file__).resolve().parent
PORT = 8888

# Shared orchestrator instance
orchestrator = MasterOrchestrator()

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Master Automation Dashboard</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151b2b;
      --card-border: #222d45;
      --accent-blue: #3b82f6;
      --accent-cyan: #06b6d4;
      --accent-purple: #8b5cf6;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-red: #ef4444;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      padding: 24px;
      line-height: 1.5;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }
    .title-group h1 {
      font-size: 26px;
      font-weight: 700;
      background: linear-gradient(135deg, #60a5fa, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .title-group p {
      color: var(--text-muted);
      font-size: 14px;
      margin-top: 4px;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
      background: #1e293b;
      border: 1px solid var(--card-border);
    }
    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent-green);
      animation: pulse 2s infinite;
    }
    .status-dot.busy { background: var(--accent-amber); }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.1); }
    }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }
    .metric-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 18px 20px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }
    .metric-value {
      font-size: 28px;
      font-weight: 700;
      margin-top: 8px;
      color: #fff;
    }
    .metric-sub {
      font-size: 12px;
      color: var(--accent-cyan);
      margin-top: 4px;
    }
    .cta-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
      border: 1px solid rgba(99, 102, 241, 0.3);
      border-radius: 14px;
      padding: 16px 20px;
      margin-bottom: 28px;
    }
    .cta-text h3 {
      font-size: 17px;
      font-weight: 600;
    }
    .cta-text p {
      font-size: 13px;
      color: var(--text-muted);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
    }
    .btn-primary {
      background: linear-gradient(135deg, #3b82f6, #6366f1);
      color: white;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    .btn-primary:hover:not(:disabled) {
      filter: brightness(1.15);
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: #1e293b;
      color: var(--text-main);
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover:not(:disabled) {
      background: #27354d;
    }
    .btn-sm {
      padding: 6px 12px;
      font-size: 12px;
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .section-title {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .platforms-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }
    .platform-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 14px;
    }
    .platform-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .platform-header h4 {
      font-size: 16px;
      font-weight: 600;
    }
    .platform-header p {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .pill {
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(16, 185, 129, 0.15);
      color: var(--accent-green);
      font-weight: 600;
    }
    .platform-stats {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 8px;
      padding: 10px;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      color: var(--text-muted);
    }
    .platform-stats strong {
      color: var(--text-main);
    }
    .platform-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .terminal-container {
      background: #050811;
      border: 1px solid var(--card-border);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 28px;
    }
    .terminal-header {
      background: #111726;
      padding: 10px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--card-border);
      font-size: 13px;
      font-weight: 600;
    }
    .terminal-body {
      padding: 14px 16px;
      height: 320px;
      overflow-y: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
      color: #38bdf8;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .terminal-body .log-line {
      margin-bottom: 2px;
    }
    .scheduler-bar {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
  </style>
</head>
<body>

  <div class="header">
    <div class="title-group">
      <h1>🚀 Master Automation Control Center</h1>
      <p>Unified Daily Engine: Naukri • Instahyre • Wellfound • PetBiz Outreach • Multi-ATS</p>
    </div>
    <div class="status-badge">
      <div id="statusDot" class="status-dot"></div>
      <span id="statusText">System Ready</span>
    </div>
  </div>

  <!-- KPI Metrics Grid -->
  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-label">Applications Sent Today</div>
      <div id="todayApps" class="metric-value">0</div>
      <div id="todayExt" class="metric-sub">+0 External Saved to CSV</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Lifetime Direct Applications</div>
      <div id="lifetimeApps" class="metric-value">0</div>
      <div id="lifetimeExt" class="metric-sub">+0 External Openings Tracked</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">PetBiz Leads Discovered</div>
      <div id="totalLeads" class="metric-value">0</div>
      <div id="withEmail" class="metric-sub">0 Verified Emails</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Client Follow-ups Due</div>
      <div id="followupsDue" class="metric-value" style="color: var(--accent-amber);">0</div>
      <div id="contactedLeads" class="metric-sub">0 Total Contacted</div>
    </div>
  </div>

  <!-- Big Run Bar -->
  <div class="cta-bar">
    <div class="cta-text">
      <h3>Run All Daily Automations Sequentially</h3>
      <p>Executes Naukri Booster (SDE+QA) ➔ Instahyre ➔ Wellfound AI Pitch ➔ PetBiz Outreach & Follow-ups</p>
    </div>
    <div style="display: flex; gap: 10px;">
      <button id="btnRunAll" class="btn btn-primary" onclick="triggerRun('all')">
        ⚡ Run Full Daily Suite
      </button>
      <button class="btn btn-secondary" onclick="exportCsv()">
        📥 Export / Refresh Master CSV
      </button>
      <button class="btn btn-secondary" onclick="loadStats()">
        🔄 Refresh
      </button>
    </div>
  </div>

  <!-- Platforms Grid -->
  <div class="section-title">📦 Automation Platforms & Individual Controls</div>
  <div class="platforms-grid">
    
    <!-- Naukri -->
    <div class="platform-card">
      <div class="platform-header">
        <div>
          <h4>1. Naukri Profile Booster & Apply</h4>
          <p>Delete & re-upload fresh resume + apply to 500 opportunities</p>
        </div>
        <span class="pill">Dual-Account</span>
      </div>
      <div class="platform-stats">
        <span>Today Direct: <strong id="nkToday">0</strong></span>
        <span>Lifetime Direct: <strong id="nkLife">0</strong></span>
        <span>CSV Exported: <strong id="nkCsv">0</strong></span>
      </div>
      <div class="platform-actions">
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('naukri_all')">Run Both (SDE + QA)</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('naukri_sde')">SDE Only</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('naukri_qa')">QA Only</button>
      </div>
    </div>

    <!-- Instahyre -->
    <div class="platform-card">
      <div class="platform-header">
        <div>
          <h4>2. Instahyre Auto-Applier</h4>
          <p>Resume bump, 1-click apply & bulk modal recommendations</p>
        </div>
        <span class="pill">Dual-Account</span>
      </div>
      <div class="platform-stats">
        <span>Today Direct: <strong id="ihToday">0</strong></span>
        <span>Lifetime Direct: <strong id="ihLife">0</strong></span>
        <span>CSV Exported: <strong id="ihCsv">0</strong></span>
      </div>
      <div class="platform-actions">
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('instahyre_all')">Run Both (SDE + QA)</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('instahyre_sde')">SDE Only</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('instahyre_qa')">QA Only</button>
      </div>
    </div>

    <!-- Wellfound -->
    <div class="platform-card">
      <div class="platform-header">
        <div>
          <h4>3. Wellfound (AngelList)</h4>
          <p>AI Gemini tailored pitch generator & stealth direct submit</p>
        </div>
        <span class="pill">AI Powered</span>
      </div>
      <div class="platform-stats">
        <span>Today Applied: <strong id="wfToday">0</strong></span>
        <span>Lifetime Applied: <strong id="wfLife">0</strong></span>
        <span>Total Tracked: <strong id="wfTot">0</strong></span>
      </div>
      <div class="platform-actions">
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('wellfound_apply')">Live Apply (10)</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('wellfound_dry')">Dry-Run Test</button>
      </div>
    </div>

    <!-- PetBiz Lead Gen -->
    <div class="platform-card">
      <div class="platform-header">
        <div>
          <h4>4. PetBiz Client Lead Gen & Outreach</h4>
          <p>Pet industry client scraper + cold outreach email sequence</p>
        </div>
        <span class="pill">Client Hunter</span>
      </div>
      <div class="platform-stats">
        <span>Total Leads: <strong id="pbLeads">0</strong></span>
        <span>Contacted: <strong id="pbContacted">0</strong></span>
        <span>Due Today: <strong id="pbDue">0</strong></span>
      </div>
      <div class="platform-actions">
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('petbiz_followup')">Send Due Follow-ups</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('petbiz_send')">Send Initial Batch (5)</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('petbiz_find')">Find Leads (Tier 1 & 2)</button>
      </div>
    </div>

    <!-- AutoApply Multi-ATS -->
    <div class="platform-card">
      <div class="platform-header">
        <div>
          <h4>5. AutoApply Multi-ATS Engine</h4>
          <p>Greenhouse, Lever, Ashby filler from external CSV leads</p>
        </div>
        <span class="pill">ATS Engine</span>
      </div>
      <div class="platform-stats">
        <span>Applied: <strong id="aaApp">0</strong></span>
        <span>Review Queue: <strong id="aaRev">0</strong></span>
        <span>Total Tracked: <strong id="aaTot">0</strong></span>
      </div>
      <div class="platform-actions">
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('autoapply_auto')">Run Auto Mode (10)</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerRun('autoapply_review')">Review Mode</button>
      </div>
    </div>

  </div>

  <!-- Live Terminal Console -->
  <div class="terminal-container">
    <div class="terminal-header">
      <span>🖥️ Live Execution Console</span>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-secondary btn-sm" onclick="clearTerminal()">Clear</button>
      </div>
    </div>
    <div id="terminalBody" class="terminal-body">
      <div class="log-line">Console initialized. Ready for automation tasks.</div>
    </div>
  </div>

  <!-- Windows Scheduled Task Card -->
  <div class="scheduler-bar">
    <div>
      <h4 style="font-size: 15px;">⏰ Windows Daily Automation Schedule (Hands-Free)</h4>
      <p id="schedulerStatus" style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
        Checking task scheduler status...
      </p>
    </div>
    <div style="display: flex; gap: 8px;">
      <button class="btn btn-secondary btn-sm" onclick="setupScheduler('09:00')">Schedule for 9:00 AM Daily</button>
      <button class="btn btn-secondary btn-sm" onclick="removeScheduler()">Disable Schedule</button>
    </div>
  </div>

  <script>
    let logInterval = null;

    async function loadStats() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        const agg = data.aggregate;
        const p = data.platforms;

        // Top Metrics
        document.getElementById('todayApps').innerText = agg.today_job_applications.toLocaleString();
        document.getElementById('todayExt').innerText = `+${agg.today_external_saved.toLocaleString()} External Saved to CSV`;
        document.getElementById('lifetimeApps').innerText = agg.lifetime_job_applications.toLocaleString();
        document.getElementById('lifetimeExt').innerText = `+${agg.lifetime_external_saved.toLocaleString()} External Openings Tracked`;
        document.getElementById('totalLeads').innerText = agg.total_client_leads.toLocaleString();
        document.getElementById('withEmail').innerText = `${agg.leads_with_email.toLocaleString()} Verified Emails`;
        document.getElementById('followupsDue').innerText = agg.client_followups_due.toLocaleString();
        document.getElementById('contactedLeads').innerText = `${agg.clients_contacted.toLocaleString()} Total Contacted`;

        // Naukri
        document.getElementById('nkToday').innerText = p.naukri.today_direct;
        document.getElementById('nkLife').innerText = p.naukri.lifetime_direct;
        document.getElementById('nkCsv').innerText = p.naukri.lifetime_external;

        // Instahyre
        document.getElementById('ihToday').innerText = p.instahyre.today_direct;
        document.getElementById('ihLife').innerText = p.instahyre.lifetime_direct;
        document.getElementById('ihCsv').innerText = p.instahyre.lifetime_external;

        // Wellfound
        document.getElementById('wfToday').innerText = p.wellfound.today_applied;
        document.getElementById('wfLife').innerText = p.wellfound.lifetime_applied;
        document.getElementById('wfTot').innerText = p.wellfound.total_tracked;

        // PetBiz
        document.getElementById('pbLeads').innerText = p.petbiz.total_leads;
        document.getElementById('pbContacted').innerText = p.petbiz.emailed_leads;
        document.getElementById('pbDue').innerText = p.petbiz.followups_due;

        // AutoApply
        document.getElementById('aaApp').innerText = p.autoapply.applied;
        document.getElementById('aaRev').innerText = p.autoapply.manual_review;
        document.getElementById('aaTot').innerText = p.autoapply.total;
      } catch (err) {
        console.error('Error loading stats:', err);
      }
    }

    async function checkStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        const dot = document.getElementById('statusDot');
        const txt = document.getElementById('statusText');
        const btnRunAll = document.getElementById('btnRunAll');

        if (data.is_running) {
          dot.className = 'status-dot busy';
          txt.innerText = `Running: ${data.current_task || 'Daily Suite'}...`;
          btnRunAll.disabled = true;
          btnRunAll.innerText = '⏳ Running Tasks...';
        } else {
          dot.className = 'status-dot';
          txt.innerText = 'System Ready';
          btnRunAll.disabled = false;
          btnRunAll.innerText = '⚡ Run Full Daily Suite';
        }
      } catch (e) {}
    }

    async function fetchLogs() {
      try {
        const res = await fetch('/api/logs');
        const logs = await res.json();
        const term = document.getElementById('terminalBody');
        term.innerHTML = logs.map(l => `<div class="log-line">${l}</div>`).join('');
        term.scrollTop = term.scrollHeight;
      } catch (e) {}
    }

    async function triggerRun(actionKey) {
      try {
        const res = await fetch('/api/run', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({action: actionKey})
        });
        const out = await res.json();
        if (out.error) {
          alert('Error: ' + out.error);
        }
        checkStatus();
      } catch (err) {
        alert('Failed to trigger task: ' + err);
      }
    }

    async function checkScheduler() {
      try {
        const res = await fetch('/api/scheduler');
        const data = await res.json();
        document.getElementById('schedulerStatus').innerText = `Task Status: ${data.status}`;
      } catch (e) {}
    }

    async function setupScheduler(timeStr) {
      try {
        const res = await fetch('/api/scheduler', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({action: 'register', time: timeStr})
        });
        const data = await res.json();
        alert(data.message);
        checkScheduler();
      } catch (e) { alert('Error: ' + e); }
    }

    async function removeScheduler() {
      try {
        const res = await fetch('/api/scheduler', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({action: 'remove'})
        });
        const data = await res.json();
        alert(data.message);
        checkScheduler();
      } catch (e) { alert('Error: ' + e); }
    }

    async function exportCsv() {
      try {
        const res = await fetch('/api/export');
        const data = await res.json();
        alert(`Successfully exported ${data.total} applications to:\n${data.path}\n(Also saved to your Desktop!)`);
      } catch (err) {
        alert('Failed to export CSV: ' + err);
      }
    }

    function clearTerminal() {
      document.getElementById('terminalBody').innerHTML = '<div class="log-line">Console cleared.</div>';
    }

    // Init polling
    loadStats();
    checkStatus();
    checkScheduler();
    fetchLogs();
    setInterval(checkStatus, 2000);
    setInterval(fetchLogs, 1500);
    setInterval(loadStats, 10000);
  </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_str, code=200):
        body = html_str.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self._send_html(HTML_TEMPLATE)
        elif url.path == "/api/stats":
            self._send_json(get_all_stats())
        elif url.path == "/api/export":
            out_p, count = export_all()
            self._send_json({"status": "OK", "total": count, "path": str(out_p)})
        elif url.path == "/api/status":
            self._send_json({
                "is_running": orchestrator.is_running,
                "current_task": orchestrator.current_task
            })
        elif url.path == "/api/logs":
            self._send_json(orchestrator.live_logs[-250:])
        elif url.path == "/api/scheduler":
            self._send_json({"status": get_task_status()})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            payload = json.loads(post_body.decode("utf-8"))
        except Exception:
            payload = {}

        if url.path == "/api/run":
            action = payload.get("action", "")
            if orchestrator.is_running:
                self._send_json({"error": "An automation task is already running!"}, code=400)
                return

            def worker():
                if action == "all":
                    orchestrator.run_daily_suite()
                elif action == "naukri_all":
                    orchestrator.run_task("naukri", ["-u", "main.py", "--all"])
                elif action == "naukri_sde":
                    orchestrator.run_task("naukri", ["-u", "main.py", "--profile", "sde"])
                elif action == "naukri_qa":
                    orchestrator.run_task("naukri", ["-u", "main.py", "--profile", "qa"])
                elif action == "instahyre_all":
                    orchestrator.run_task("instahyre", ["-u", "main.py", "--all"])
                elif action == "instahyre_sde":
                    orchestrator.run_task("instahyre", ["-u", "main.py", "--profile", "sde"])
                elif action == "instahyre_qa":
                    orchestrator.run_task("instahyre", ["-u", "main.py", "--profile", "qa"])
                elif action == "wellfound_apply":
                    orchestrator.run_task("wellfound", ["-u", "main.py", "--apply", "--limit", "10"])
                elif action == "wellfound_dry":
                    orchestrator.run_task("wellfound", ["-u", "main.py", "--dry-run", "--limit", "5"])
                elif action == "petbiz_followup":
                    orchestrator.run_task("petbiz", ["-u", "cli.py", "followup", "--limit", "10", "--force-real"])
                elif action == "petbiz_send":
                    orchestrator.run_task("petbiz", ["-u", "cli.py", "send", "--limit", "5", "--force-real"])
                elif action == "petbiz_find":
                    orchestrator.run_task("petbiz", ["-u", "cli.py", "find", "--cities", "Mumbai,Pune,Bengaluru,Delhi", "--limit", "10"])
                elif action == "autoapply_auto":
                    orchestrator.run_task("autoapply", ["-u", "run_applier.py", "--mode", "auto", "--limit", "10"])
                elif action == "autoapply_review":
                    orchestrator.run_task("autoapply", ["-u", "run_applier.py", "--mode", "review", "--limit", "5"])

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            self._send_json({"status": "STARTED", "action": action})

        elif url.path == "/api/scheduler":
            action = payload.get("action", "")
            if action == "register":
                t_str = payload.get("time", "09:00")
                ok, msg = register_windows_task(t_str)
                self._send_json({"success": ok, "message": msg})
            elif action == "remove":
                ok, msg = remove_windows_task()
                self._send_json({"success": ok, "message": msg})
            else:
                self._send_json({"error": "Unknown scheduler action"}, code=400)
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=PORT):
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"\n==================================================================")
    print(f"  🌐 MASTER AUTOMATION WEB CONTROL CENTER RUNNING")
    print(f"  👉 Open URL in browser: http://localhost:{port}")
    print(f"==================================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web dashboard server...")
        server.server_close()

if __name__ == "__main__":
    run_server()
