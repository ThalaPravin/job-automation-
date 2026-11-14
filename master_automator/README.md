# 🎛️ Master Automation & Daily Routine Orchestrator

One unified command center and web dashboard to run, schedule, and monitor all your job application automation engines (**Wellfound**, **Naukri**, and **Instahyre**) from a single interface.

---

## 🌟 Key Capabilities

1. **Unified Multi-Platform Execution**:
   - Run daily routines across all platforms sequentially with configurable cooldown periods.
   - Run individual platforms or specific career tracks on demand.
2. **Modern Web Dashboard (`http://localhost:8888`)**:
   - Built-in lightweight local web UI displaying real-time metrics, lifetime application totals, and live output streaming.
   - 1-click execution buttons for single platforms or full suites.
3. **Consolidated CSV Export**:
   - Aggregates applied job histories and exported ATS links across all platforms into one master spreadsheet (`all_job_applications.csv`).
4. **Interactive CLI & Windows Scheduler**:
   - Terminal interactive menu (`python master_cli.py`) for quick manual triggering or automated daily cron / Windows Task Scheduler setup.

---

## 📁 Directory Structure

```text
master_automator/
├── config.example.json   # Multi-project paths, cooldowns, and scheduler configurations
├── orchestrator.py       # Sequential process execution engine with real-time log piping
├── master_cli.py         # Rich interactive command-line interface
├── web_server.py         # Local web UI server (Dashboard on localhost:8888)
├── stats_collector.py    # Multi-platform database parser & metric consolidator
├── scheduler_manager.py  # Automated scheduler manager
├── export_master_csv.py  # Consolidated CSV exporter
├── LAUNCH_DASHBOARD.bat  # 1-click interactive CLI launcher
├── LAUNCH_WEB_UI.bat     # 1-click web control center launcher
├── RUN_DAILY_ALL.bat     # 1-click full daily automation suite launcher
└── README.md
```

---

## 🚀 Setup & Usage

### 1. Configure (`config.json`)
Copy the configuration template:
```bash
copy config.example.json config.json
```
Ensure the project paths in `config.json` point to your platform folders:
- `"naukri"`: `"../naukri"`
- `"instahyre"`: `"../instahyre"`
- `"wellfound"`: `"../wellfound"`

### 2. Launch Interactive Command Center
```bash
python master_cli.py
# (or double-click LAUNCH_DASHBOARD.bat)
```

### 3. Launch Web Dashboard
```bash
python web_server.py
# (or double-click LAUNCH_WEB_UI.bat)
```
Open your browser to `http://localhost:8888`.

### 4. Run Full Daily Suite
```bash
python master_cli.py --daily
# (or double-click RUN_DAILY_ALL.bat)
```
