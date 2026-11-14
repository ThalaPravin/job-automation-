# 🚀 Unified Job Application Automation Suite
### Automated Job Search, Resume Boosting, and Application Engine for Wellfound, Naukri & Instahyre

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Multi-Platform](https://img.shields.io/badge/Platforms-Wellfound%20%7C%20Naukri%20%7C%20Instahyre-brightgreen.svg)](#-connected-platforms)

A battle-tested, modular automation suite engineered with **Playwright**, **Python**, and **AI Pitch Generation**. It unifies three major hiring platforms into one seamless command center—handling daily profile bumping, recruiter search optimization, 1-click auto-applies, tailored AI pitches, and cross-platform deduplication.

---

## 📦 Connected Platforms

| Platform | Folder | Core Automation Features | Daily Target | Target Market |
| :--- | :--- | :--- | :--- | :--- |
| **Wellfound** *(AngelList)* | [`wellfound/`](wellfound/) | AI tailored pitch generation (Gemini), anti-bot stealth Playwright, 1,000-char note limits, deduplication | 10–20 apps/day | US, Global Startups, Remote |
| **Naukri.com** | [`naukri/`](naukri/) | Automated resume delete + re-upload (bumping profile to "Active in <24h"), dual-profile (SDE & QA), direct 1-click applies + external ATS link export | 50 direct / 500 total | India Tech, MNCs, High-Growth |
| **Instahyre** | [`instahyre/`](instahyre/) | High-speed 1-click direct apply, automated questionnaire answering, bulk modal recommendations, dual-profile (SDE & QA) | Up to 300 direct / 600 total | Top Funded Startups, Unicorns |
| **Master Automator** | [`master_automator/`](master_automator/) | Local Web Dashboard (`localhost:8888`), sequential multi-platform orchestrator, consolidated CSV export, Windows Task Scheduler | Daily Suite | Hands-Free Routine |

---

## 🌟 Key Architecture & Anti-Detection Features

1. **Persistent Browser Sessions (`browser_profile/`)**:
   - Log in **once** manually in a visible Chromium window. Cookies, local storage, and 2FA tokens are saved locally. No hardcoded passwords, tokens, or credential leaks.
2. **Stealth & Bot Evasion**:
   - Uses real Chromium user-agents, window maximization, and injected stealth scripts removing `navigator.webdriver` flags to pass Cloudflare Turnstile and anti-bot checks.
3. **Resume Freshness Bump (Naukri & Instahyre)**:
   - Recruiter search engines (e.g. Naukri Resdex) rank profiles by recent activity. The engine executes a strict delete-and-reupload sequence every morning so you appear under **"Active in < 24 Hours"**.
4. **Tailored AI Pitch Generation (Wellfound)**:
   - Generates high-converting startup pitch notes under 1,000 characters using Google Gemini or customizable markdown templates.
5. **SQLite Deduplication & State Tracking**:
   - Every platform tracks applied job keys in a local SQLite database (`data/*.db`). You will never apply to the same role twice.
6. **Consolidated CSV Export**:
   - Collects external application links (Workday, Greenhouse, Lever, Ashby) across all platforms into one master spreadsheet (`all_job_applications.csv`).

---

## 📁 Repository Structure

```text
job-automation/
├── wellfound/                  # Wellfound (AngelList) Automation Engine
│   ├── config/                 # Profile & search config templates
│   ├── src/                    # Applier, browser, auth, pitcher, and DB logic
│   ├── main.py                 # Wellfound CLI runner
│   ├── apply.bat               # 1-click live apply
│   ├── dry_run.bat             # 1-click safe dry-run test
│   ├── login.bat               # 1-click one-time session login
│   └── README.md
│
├── naukri/                     # Naukri.com Multi-Profile Automation
│   ├── config.example.yaml     # Roles, quotas, experience, and screening answers
│   ├── browser_manager.py      # Playwright persistent context manager
│   ├── job_engine.py           # Feed discovery & 1-click apply engine
│   ├── profile_updater.py      # Resume delete/re-upload & profile touch flow
│   ├── database.py             # SQLite deduplication
│   ├── setup_session.py        # One-time interactive session login
│   ├── main.py                 # Naukri CLI runner
│   ├── run_all.bat             # Run both SDE & QA tracks
│   └── README.md
│
├── instahyre/                  # Instahyre Multi-Profile Automation
│   ├── config.example.yaml     # Skills, roles, and screening questionnaire answers
│   ├── browser_manager.py      # Playwright persistent context manager
│   ├── job_engine.py           # 1-click applicant & recommendation modal handler
│   ├── profile_updater.py      # Profile freshness and resume upload engine
│   ├── database.py             # SQLite deduplication
│   ├── setup_session.py        # One-time interactive session login
│   ├── generate_html_report.py # Visual HTML application report generator
│   ├── main.py                 # Instahyre CLI runner
│   ├── run_all.bat             # Run both SDE & QA tracks
│   └── README.md
│
├── master_automator/           # Orchestrator & Web Control Center
│   ├── config.example.json     # Multi-project relative path config
│   ├── orchestrator.py         # Sequential execution engine with live log streaming
│   ├── web_server.py           # Web UI server (http://localhost:8888)
│   ├── master_cli.py           # Interactive rich terminal command center
│   ├── stats_collector.py      # Consolidated multi-platform statistics
│   ├── export_master_csv.py    # Master CSV exporter
│   ├── LAUNCH_DASHBOARD.bat    # 1-click CLI dashboard launcher
│   ├── LAUNCH_WEB_UI.bat       # 1-click web control center launcher
│   ├── RUN_DAILY_ALL.bat       # 1-click full daily suite launcher
│   └── README.md
│
├── main.py                     # Master CLI dispatcher for all 3 platforms
├── RUN_ALL_DAILY.bat           # Root 1-click daily suite launcher
├── LAUNCH_WEB_UI.bat           # Root 1-click web UI launcher
├── LAUNCH_DASHBOARD.bat        # Root 1-click CLI menu launcher
├── RUN_NAUKRI.bat              # Root 1-click Naukri launcher
├── RUN_INSTAHYRE.bat           # Root 1-click Instahyre launcher
├── apply.bat                   # Root 1-click Wellfound launcher
├── requirements.txt            # Unified dependencies
├── .gitignore                  # Comprehensive rules ignoring all private data
├── LICENSE                     # MIT License
└── README.md                   # Master documentation
```

---

## ⚡ Quick Start & Setup

### 1. Prerequisites
- **Python 3.10+**
- **Google Chrome** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/ThalaPravin/job-automation-.git
cd job-automation-
```

### 3. Set Up Virtual Environment & Dependencies
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

## ⚙️ Platform Configuration

Each platform contains a clean `.example.` configuration file. Simply copy and fill in your details:

### 1. Wellfound Configuration
```bash
copy wellfound\config\profile.example.yaml wellfound\config\profile.yaml
copy wellfound\config\config.example.yaml wellfound\config\config.yaml
```
- In `wellfound/config/profile.yaml`: Fill in your candidate details, primary skills, portfolio/GitHub links, and master pitch note template.
- Optional: Add your Google Gemini API key to `.env` if you want AI-generated notes.

### 2. Naukri Configuration
```bash
copy naukri\config.example.yaml naukri\config.yaml
```
- In `naukri/config.yaml`: Set the paths to your PDF resumes for SDE and QA tracks, and configure your salary/notice period answers.

### 3. Instahyre Configuration
```bash
copy instahyre\config.example.yaml instahyre\config.yaml
```
- In `instahyre/config.yaml`: Set target skills, target roles, experience range, and questionnaire answers.

### 4. Master Automator Configuration
```bash
copy master_automator\config.example.json master_automator\config.json
```

---

## 🚦 How to Run

### Option 1: 1-Click Launchers (Windows)
Double-click any of the batch files in the root folder:
- **`RUN_ALL_DAILY.bat`**: Runs the entire multi-platform daily automation sequentially.
- **`LAUNCH_WEB_UI.bat`**: Opens the Web Control Center at `http://localhost:8888`.
- **`LAUNCH_DASHBOARD.bat`**: Opens the interactive terminal dashboard menu.
- **`apply.bat`**: Runs Wellfound Live Apply.
- **`RUN_NAUKRI.bat`**: Runs Naukri SDE & QA automation.
- **`RUN_INSTAHYRE.bat`**: Runs Instahyre SDE & QA automation.

---

### Option 2: Unified Command-Line Interface (CLI)
From the repository root:
```bash
# Run the complete daily suite (all 3 platforms)
python main.py --all

# Launch the Web Dashboard
python main.py --dashboard

# Run Wellfound automation
python main.py --wellfound --apply --limit 10
python main.py --wellfound --stats

# Run Naukri automation
python main.py --naukri --all
python main.py --naukri --profile sde

# Run Instahyre automation
python main.py --instahyre --all
python main.py --instahyre --profile sde
```

---

### Option 3: Modern Web Control Center (`http://localhost:8888`)
Launch the web server:
```bash
python main.py --dashboard
# (or double-click LAUNCH_WEB_UI.bat)
```
Open **`http://localhost:8888`** in your browser:
- Real-time metric cards (Daily applications, lifetime total, external leads).
- One-click **"⚡ Run Full Daily Suite"** button.
- Platform-specific triggers (Wellfound, Naukri SDE/QA, Instahyre SDE/QA).
- Live terminal execution console.

---

## ⏰ Automated Hands-Free Routine (Windows Task Scheduler)

To run the complete job application suite automatically every morning at **9:00 AM** without touching your computer:

Open **PowerShell as Administrator** and run:
```powershell
$Action = New-ScheduledTaskAction -Execute "$PWD\RUN_ALL_DAILY.bat"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "DailyMasterJobAutomation" -Description "Automated daily resume boost and multi-platform job application suite"
```

---

## 🔒 Security & Privacy Notice

- **No Credentials in Code**: All personal profiles (`profile.yaml`), configurations (`config.yaml`, `config.json`), API keys (`.env`), and session directories (`browser_profile*`) are strictly ignored by `.gitignore`.
- **Safe Quotas**: Respect platform limits to keep your accounts in good standing:
  - Wellfound: 10–20 applications daily.
  - Naukri: 50 direct applications daily (Naukri platform maximum).
  - Instahyre: 200–300 applications daily.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
