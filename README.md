# 🤖 Wellfound (AngelList) Job Application Automation

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, safety-first job search and application automation bot for **Wellfound** (formerly AngelList Talent). Powered by **Playwright**, **Python**, and customizable **AI Pitch Generation** (Gemini / templating).

Designed to automate repetitive job discovery and custom note submission while keeping your account completely secure with human-like browsing patterns, persistent sessions, and automated deduplication.

---

## 🌟 Key Features

- **🔐 Persistent Authentication**: Log in once manually in a real browser session; cookies, local storage, and session tokens are preserved locally in `browser_profile/`. No hardcoded credentials or repeated 2FA.
- **🛡️ Stealth & Anti-Bot Evasion**: Runs real Chromium with stealth scripts to mask `navigator.webdriver` flags, simulating organic human interactions.
- **⏱️ Humanized Randomized Pacing**: Configurable delays (default: 15–35 seconds) between applications prevent account rate-limiting or anti-bot flags.
- **📝 High-Impact Pitch Generation**: Generates customized, high-converting pitch notes (under 1,000 characters) tailored to company and role requirements via Google Gemini or customizable markdown templates.
- **🗄️ SQLite Deduplication**: Tracks every job application in a local SQLite database (`data/applications.db`). You will never accidentally apply to the same company or position twice.
- **🧪 Safe Dry-Run Mode**: Inspect discovered jobs, preview generated pitch notes, and take debug screenshots without submitting live applications.
- **📊 Real-Time Analytics**: Built-in CLI command to review total applications, recent companies, statuses, and timestamps.

---

## 📁 Project Structure

```text
job-automation/
├── config/
│   ├── config.example.yaml     # Search filters, daily limits, pacing, and blacklist rules
│   └── profile.example.yaml    # Candidate profile, skills, links, screening answers & pitch template
├── src/
│   ├── ai_pitcher.py           # Gemini AI and dynamic template pitch generator
│   ├── applier.py              # Wellfound feed navigator, modal handler, and application engine
│   ├── auth.py                 # Interactive & automated login detection
│   ├── browser.py              # Playwright persistent context & stealth manager
│   ├── config_loader.py        # Pydantic schemas and YAML configuration loader
│   └── db.py                   # SQLite database manager for tracking & deduplication
├── data/
│   └── .gitkeep                # Applications database and screenshots directory (local-only)
├── .env.example                # Optional Gemini API key configuration
├── .gitignore                  # Strict rules to ignore credentials, profiles, and databases
├── apply.bat                   # 1-click batch script for live application runs
├── dry_run.bat                 # 1-click batch script for safe dry-run tests
├── login.bat                   # 1-click batch script for initial browser login
├── main.py                     # Main CLI entrypoint
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- **Google Chrome** installed (optional, but recommended for native Chromium channel).

### 2. Clone the Repository
```bash
git clone https://github.com/ThalaPravin/job-automation-.git
cd job-automation-
```

### 3. Set Up Virtual Environment
On Windows (PowerShell / Command Prompt):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## ⚙️ Configuration

Before running, configure your candidate profile and search preferences:

### Step 1: Candidate Profile (`config/profile.yaml`)
Copy the example template:
```bash
# Windows
copy config\profile.example.yaml config\profile.yaml

# macOS / Linux
cp config/profile.example.yaml config/profile.yaml
```
Open `config/profile.yaml` in your text editor and fill in your details:
- **`candidate`**: Full name, email, phone, location, GitHub, Portfolio, LinkedIn, primary tech stack, and summary.
- **`pitch`**: Customize your master application pitch note template. You can use dynamic variables like `{company_name}`, `{role_title}`, `{candidate_name}`, `{skills}`, `{portfolio}`, `{github}`, `{linkedin}`.
- **`screening_answers`**: Your standard answers for common startup screening questions (work authorization, notice period, salary expectations).

### Step 2: Search & Safety Filters (`config/config.yaml`)
Copy the configuration template:
```bash
# Windows
copy config\config.example.yaml config\config.yaml

# macOS / Linux
cp config/config.example.yaml config/config.yaml
```
Key settings to customize:
- **`custom_search_url`**: *(Recommended)* Go to [wellfound.com/jobs](https://wellfound.com/jobs) in your browser, apply your target filters (Roles, Remote, Salary, Tech Stack), and paste the full resulting URL into `custom_search_url`.
- **`max_applications_per_run`**: Maximum number of applications per batch (recommended: 10–15).
- **`min_delay_seconds` & `max_delay_seconds`**: Randomized human delay between applications (default: 15–35 seconds).
- **`blacklist`**: Companies or title keywords (e.g., `Intern`, `Staff`, `VP`, `Unpaid`) to automatically skip.

### Step 3: (Optional) AI Pitch Generation with Gemini
If you want Google Gemini to write hyper-tailored pitch notes for each job description:
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
2. Add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. In `config/profile.yaml`, set `pitch.use_ai: true`.

*(Note: If `use_ai` is `false` or no API key is set, the bot uses your customized pitch template from `config/profile.yaml`)*.

---

## 🎮 How to Use

### 1. One-Time Login (Save Session)
Run the login command to launch the browser:
```bash
# Using CLI
python main.py --login

# Or on Windows, double-click:
login.bat
```
- A visible browser window will open to Wellfound.
- Sign in with Google, LinkedIn, or Email + Password.
- Once you are logged in and see the Wellfound dashboard, press `ENTER` in your terminal.
- Your session is saved locally in `browser_profile/` for all future automated runs.

---

### 2. Run in Dry-Run Mode (Safe Test)
Test job scanning, modal opening, and pitch generation without submitting:
```bash
# Test 3 applications in dry-run mode
python main.py --dry-run --limit 3

# Or on Windows:
dry_run.bat
```
- The bot will navigate to your search feed, extract matching job cards, fill in the pitch note, take a screenshot to `data/screenshots/`, and close the modal without clicking Submit.

---

### 3. Live Apply
When you are satisfied with your pitch notes and configuration:
```bash
# Live apply to 10 matching jobs
python main.py --apply --limit 10

# Or on Windows:
apply.bat
```
The bot will:
1. Verify existing session.
2. Scan the jobs feed according to your `custom_search_url`.
3. Check company and title against your blacklist.
4. Verify whether you have previously applied via the local SQLite database.
5. Fill the customized pitch note.
6. Click Submit.
7. Record the application timestamp in `data/applications.db`.
8. Wait for a randomized human delay (15–35s) before processing the next role.

---

### 4. View Application Statistics & History
To see how many jobs you have applied to and view recent submissions:
```bash
python main.py --stats
```

Example output:
```text
=== Application Statistics ===
┌─────────┬───────┐
│ Status  │ Count │
├─────────┼───────┤
│ TOTAL   │    23 │
│ APPLIED │    22 │
│ DRY_RUN │     1 │
│ SKIPPED │     0 │
│ FAILED  │     0 │
└─────────┴───────┘
```

---

## 🔒 Security & Privacy Notice

- **Never Commit Secrets**: `config/profile.yaml`, `config/config.yaml`, `.env`, `browser_profile/`, and `data/*.db` are strictly ignored by `.gitignore`. Keep your personal profile and session tokens on your local machine.
- **Account Safety Guidelines**:
  - Do not exceed 20–30 applications per 24-hour window to avoid triggering Wellfound rate limits.
  - Always keep `headless: false` in `config/config.yaml` so Cloudflare anti-bot challenges can render naturally without getting flagged.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
