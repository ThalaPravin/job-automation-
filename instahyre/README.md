# ⚡ Instahyre Multi-Profile Job Automation Engine

An intelligent, high-speed job discovery and 1-click application automation engine for **Instahyre.com**. Built with **Playwright**, **Python**, and SQLite deduplication, tailored for both **Software Development (SDE)** and **Quality Assurance (QA/SDET)** roles.

---

## 🌟 Key Features

1. **Daily 1-Click In-Platform Direct Apply**:
   - Automatically navigates matching job cards on Instahyre.
   - Triggers the 1-click apply button, answers screening questionnaires automatically, and handles post-application bulk recommendation modals.
2. **Multi-Profile Architecture (SDE & QA Tracks)**:
   - Dedicated browser sessions (`browser_profile_sde/`, `browser_profile_qa/`) and configurations to optimize ATS matching without keyword cross-contamination.
3. **Automated Resume Freshness Bump**:
   - Touches and refreshes candidate profile timestamps daily to guarantee priority placement in recruiter talent searches.
4. **External ATS Link Capture**:
   - Collects roles directing to external portals (Workday, Greenhouse, Lever) and exports clean structured CSVs (`data/external_jobs_sde.csv`).
5. **Interactive HTML Reporting**:
   - Built-in script `generate_html_report.py` visualizes application volume, company distributions, and tracking history.

---

## 📁 Directory Structure

```text
instahyre/
├── config.example.yaml     # Search skills, roles, screening answers, and quotas
├── browser_manager.py      # Playwright Chromium persistent context & stealth manager
├── job_engine.py           # Feed navigator, 1-click applicant, and modal handler
├── profile_updater.py      # Profile freshness and resume upload engine
├── database.py             # SQLite deduplication and history tracking
├── setup_session.py        # Interactive one-time session login saver
├── stats.py                # Command-line analytics and statistics tool
├── generate_html_report.py # Interactive HTML dashboard generator
├── main.py                 # Main CLI runner
├── run_all.bat             # 1-click execution for both SDE and QA profiles
├── run_sde.bat             # 1-click execution for SDE profile only
├── run_qa.bat              # 1-click execution for QA profile only
├── setup_sde.bat           # 1-click login setup for SDE
├── setup_qa.bat            # 1-click login setup for QA
└── README.md
```

---

## 🚀 Setup & Usage

### 1. Configure Profiles (`config.yaml`)
Copy the configuration template:
```bash
copy config.example.yaml config.yaml
```
Open `config.yaml` and configure:
- `resume_path`: Path to your PDF resume.
- Target `skills` and `roles`.
- `screening_answers`: Experience, expected CTC, notice period, and relocation willingness.

### 2. One-Time Login
Save your persistent browser sessions:
```bash
# For SDE Profile
python setup_session.py --profile sde
# (or double-click setup_sde.bat)

# For QA Profile
python setup_session.py --profile qa
# (or double-click setup_qa.bat)
```
Log into your Instahyre account in the opened Chromium window and press **ENTER** in your terminal.

### 3. Run Automation
```bash
# Run SDE Profile only
python main.py --profile sde
# (or run_sde.bat)

# Run QA Profile only
python main.py --profile qa
# (or run_qa.bat)

# Run BOTH profiles sequentially
python main.py --all
# (or run_all.bat)
```

### 4. Check Analytics
```bash
python stats.py
# (or check_stats.bat)
```
To generate an interactive HTML report:
```bash
python generate_html_report.py
```
