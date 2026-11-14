# 🇮🇳 Naukri Multi-Profile Automation & Profile Booster

An automated, anti-detection job application and profile boosting engine for **Naukri.com**. It automates daily resume deletion & re-upload (bumping your profile to the top of recruiter searches in Resdex) and processes up to **500 job opportunities daily** across both **Software Development (SDE)** and **Quality Assurance (QA/SDET)** roles.

---

## 🌟 Key Features

1. **Daily Resume Refresh & Profile Timestamp Bump**:
   - Recruiter search algorithms prioritize candidates active in the last 24 hours.
   - The engine automatically deletes the old resume, uploads the fresh file, verifies upload confirmation, and touches profile summary fields so your profile appears under **"Active in < 24 Hours"**.
2. **Dual-Profile Support (SDE & QA Tracks)**:
   - Separate configurations and isolated browser sessions (`browser_profile_sde`, `browser_profile_qa`) for targeting distinct career tracks without diluting keyword relevance.
3. **Automated Direct Application & External Lead Export**:
   - Submits in-platform 1-click applications up to the daily platform quota (50 applications).
   - Automatically parses and exports external company application URLs (Greenhouse, Lever, Workday) into clean CSV files (`data/external_jobs_sde.csv`).
4. **Intelligent Deduplication**:
   - SQLite database tracks every processed job ID to guarantee you never re-apply to the same opening.

---

## 📁 Directory Structure

```text
naukri/
├── config.example.yaml   # Search roles, screening answers, quotas, and blacklist filters
├── browser_manager.py    # Playwright Chromium persistent context & stealth manager
├── job_engine.py         # Feed scanner, job modal parser, and application engine
├── profile_updater.py    # Automated resume delete/re-upload and timestamp touch flow
├── database.py           # SQLite deduplication and history tracking
├── setup_session.py      # One-time interactive browser login session saver
├── stats.py              # CLI statistics & reporting tool
├── main.py               # Main CLI runner
├── run_all.bat           # 1-click execution for both SDE and QA profiles
├── run_sde.bat           # 1-click execution for SDE profile only
├── run_qa.bat            # 1-click execution for QA profile only
├── setup_session.bat     # 1-click browser login launcher
└── README.md
```

---

## 🚀 Setup & Usage

### 1. Configure Profiles (`config.yaml`)
Copy the configuration template:
```bash
copy config.example.yaml config.yaml
```
Edit `config.yaml`:
- Set `resume_path` to the location of your PDF resume.
- Update target roles and screening answers (experience, current/expected CTC, notice period).

### 2. One-Time Login
Save your persistent browser session:
```bash
# For SDE Profile
python setup_session.py --profile sde
# (or double-click setup_session.bat)

# For QA Profile
python setup_session.py --profile qa
# (or double-click setup_qa.bat)
```
A Chromium window will open. Log into your Naukri account manually, then press **ENTER** in your terminal. Your session will be saved in `browser_profile_sde/` (or `browser_profile_qa/`).

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
