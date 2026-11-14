"""
Generates an interactive HTML dashboard to visualize all applied and saved jobs across SDE & QA profiles in your web browser.
"""

import os
import sqlite3
import webbrowser
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_report():
    sde_db = os.path.join(BASE_DIR, "data", "instahyre_sde.db")
    qa_db = os.path.join(BASE_DIR, "data", "instahyre_qa.db")
    sde_csv = os.path.join(BASE_DIR, "data", "external_jobs_sde.csv")
    qa_csv = os.path.join(BASE_DIR, "data", "external_jobs_qa.csv")
    output_html = os.path.join(BASE_DIR, "dashboard.html")

    jobs = []
    total_direct_applied = 0
    total_external_saved = 0
    sde_direct = 0
    qa_direct = 0

    profiles_to_read = [
        ("SDE", sde_db),
        ("QA", qa_db)
    ]

    for p_name, db_file in profiles_to_read:
        if os.path.exists(db_file):
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("""
                SELECT job_id, title, company, experience, location, job_url, apply_type, status, created_at 
                FROM applied_jobs 
                ORDER BY created_at DESC 
            """)
            for row in c.fetchall():
                status = row[7]
                jobs.append({
                    "profile": p_name,
                    "id": row[0],
                    "title": row[1],
                    "company": row[2],
                    "exp": row[3],
                    "loc": row[4],
                    "url": row[5],
                    "type": row[6],
                    "status": status,
                    "date": str(row[8])[:16]
                })
                if status == "APPLIED":
                    total_direct_applied += 1
                    if p_name == "SDE":
                        sde_direct += 1
                    else:
                        qa_direct += 1
                elif status == "SAVED_TO_CSV":
                    total_external_saved += 1
            conn.close()

    # Sort all jobs by date descending
    jobs.sort(key=lambda x: x["date"], reverse=True)

    # Count rows in CSVs
    sde_csv_count = 0
    if os.path.exists(sde_csv):
        with open(sde_csv, "r", encoding="utf-8", errors="ignore") as f:
            sde_csv_count = max(0, len(f.readlines()) - 1)

    qa_csv_count = 0
    if os.path.exists(qa_csv):
        with open(qa_csv, "r", encoding="utf-8", errors="ignore") as f:
            qa_csv_count = max(0, len(f.readlines()) - 1)

    total_csv_openings = sde_csv_count + qa_csv_count

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instahyre Unified Applications Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #0f172a;
            color: #f1f5f9;
            padding: 32px 20px;
        }}
        .container {{
            max-width: 1280px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 28px;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .title h1 {{
            font-size: 26px;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 4px;
        }}
        .title p {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .instahyre-btn {{
            background: #2563eb;
            color: #fff;
            padding: 10px 18px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }}
        .instahyre-btn:hover {{
            background: #1d4ed8;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .stat-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
        }}
        .stat-card .label {{
            font-size: 13px;
            font-weight: 500;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .stat-card .val {{
            font-size: 28px;
            font-weight: 700;
            color: #f8fafc;
        }}
        .stat-card .subtext {{
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
        }}
        .stat-card.highlight {{
            border-color: #38bdf8;
            background: linear-gradient(135deg, #1e293b 0%, #0f2b48 100%);
        }}
        .stat-card.highlight .val {{
            color: #38bdf8;
        }}
        .stat-card.highlight-green {{
            border-color: #10b981;
            background: linear-gradient(135deg, #1e293b 0%, #064e3b 100%);
        }}
        .stat-card.highlight-green .val {{
            color: #34d399;
        }}
        .controls-bar {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .search-bar {{
            flex: 1;
            min-width: 250px;
        }}
        .search-bar input {{
            width: 100%;
            padding: 12px 16px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-bar input:focus {{
            border-color: #38bdf8;
        }}
        .filter-buttons {{
            display: flex;
            gap: 8px;
        }}
        .filter-btn {{
            padding: 10px 16px;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #94a3b8;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .filter-btn.active, .filter-btn:hover {{
            background: #38bdf8;
            color: #0f172a;
            border-color: #38bdf8;
        }}
        .table-wrap {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        thead {{
            background: #0f172a;
            border-bottom: 1px solid #334155;
        }}
        th {{
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        tbody tr {{
            border-bottom: 1px solid #334155;
            transition: background 0.15s;
        }}
        tbody tr:hover {{
            background: #273549;
        }}
        td {{
            padding: 14px 16px;
            color: #cbd5e1;
        }}
        td.title {{
            font-weight: 600;
            color: #f1f5f9;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge.applied {{
            background: #064e3b;
            color: #34d399;
            border: 1px solid #059669;
        }}
        .badge.csv {{
            background: #1e3a8a;
            color: #60a5fa;
            border: 1px solid #2563eb;
        }}
        .badge.profile-sde {{
            background: #312e81;
            color: #a5b4fc;
            border: 1px solid #4f46e5;
        }}
        .badge.profile-qa {{
            background: #581c87;
            color: #d8b4fe;
            border: 1px solid #9333ea;
        }}
        .job-link {{
            color: #38bdf8;
            text-decoration: none;
            font-weight: 500;
        }}
        .job-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <h1>Instahyre Applications Dashboard</h1>
                <p>Tracking SDE (Java, Golang, Backend) and QA / SDET (Automation, Manual Testing) | 0-3 Years Exp</p>
            </div>
            <a href="https://www.instahyre.com/candidate/opportunities/" target="_blank" class="instahyre-btn">
                Open Instahyre Portal &rarr;
            </a>
        </div>

        <div class="stats-grid">
            <div class="stat-card highlight-green">
                <div class="label">Total Direct Applied</div>
                <div class="val">{total_direct_applied}</div>
                <div class="subtext">SDE: {sde_direct} | QA: {qa_direct}</div>
            </div>
            <div class="stat-card highlight">
                <div class="label">External Openings in CSV</div>
                <div class="val">{total_csv_openings}</div>
                <div class="subtext">SDE: {sde_csv_count} | QA: {qa_csv_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Database Records</div>
                <div class="val">{len(jobs)}</div>
                <div class="subtext">Deduplicated across profiles</div>
            </div>
            <div class="stat-card">
                <div class="label">Combined Opportunities</div>
                <div class="val">{total_direct_applied + total_csv_openings}</div>
                <div class="subtext">Direct Submissions + Career Links</div>
            </div>
        </div>

        <div class="controls-bar">
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="Search by title, company, location, or skill..." onkeyup="filterTable()">
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="setProfileFilter('ALL', this)">All</button>
                <button class="filter-btn" onclick="setProfileFilter('SDE', this)">SDE Only</button>
                <button class="filter-btn" onclick="setProfileFilter('QA', this)">QA Only</button>
                <button class="filter-btn" onclick="setStatusFilter('APPLIED', this)">Applied Only</button>
            </div>
        </div>

        <div class="table-wrap">
            <table id="jobsTable">
                <thead>
                    <tr>
                        <th>Track</th>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Location</th>
                        <th>Experience</th>
                        <th>Status</th>
                        <th>Date Processed</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    """

    for j in jobs:
        badge_cls = "applied" if j["status"] == "APPLIED" else "csv"
        badge_txt = "Applied In-Platform" if j["status"] == "APPLIED" else "Saved in CSV"
        p_badge_cls = "profile-sde" if j["profile"] == "SDE" else "profile-qa"
        
        html_content += f"""
                    <tr data-profile="{j['profile']}" data-status="{j['status']}">
                        <td><span class="badge {p_badge_cls}">{j['profile']}</span></td>
                        <td class="title">{j['title']}</td>
                        <td class="company">{j['company']}</td>
                        <td>{j['loc']}</td>
                        <td>{j['exp']}</td>
                        <td><span class="badge {badge_cls}">{badge_txt}</span></td>
                        <td>{j['date']}</td>
                        <td><a href="{j['url']}" target="_blank" class="job-link">View Listing &rarr;</a></td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let currentProfileFilter = 'ALL';
        let currentStatusFilter = 'ALL';

        function setProfileFilter(val, btn) {
            currentProfileFilter = val;
            updateFilterButtons(btn);
            applyFilters();
        }

        function setStatusFilter(val, btn) {
            if (currentStatusFilter === val) {
                currentStatusFilter = 'ALL';
                btn.classList.remove('active');
            } else {
                currentStatusFilter = val;
                btn.classList.add('active');
            }
            applyFilters();
        }

        function updateFilterButtons(activeBtn) {
            const btns = document.querySelectorAll('.filter-buttons .filter-btn');
            btns.forEach(b => {
                if (b.textContent.includes('Only') || b.textContent === 'All') {
                    b.classList.remove('active');
                }
            });
            activeBtn.classList.add('active');
        }

        function filterTable() {
            applyFilters();
        }

        function applyFilters() {
            const input = document.getElementById("searchInput");
            const filter = input.value.toLowerCase();
            const table = document.getElementById("jobsTable");
            const tr = table.getElementsByTagName("tr");

            for (let i = 1; i < tr.length; i++) {
                const row = tr[i];
                const pVal = row.getAttribute("data-profile");
                const sVal = row.getAttribute("data-status");
                const text = (row.textContent || row.innerText).toLowerCase();

                let matchesText = text.indexOf(filter) > -1;
                let matchesProfile = (currentProfileFilter === 'ALL' || pVal === currentProfileFilter);
                let matchesStatus = (currentStatusFilter === 'ALL' || sVal === currentStatusFilter);

                if (matchesText && matchesProfile && matchesStatus) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            }
        }
    </script>
</body>
</html>
    """

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Unified Dashboard HTML generated: {output_html}")
    return output_html

if __name__ == "__main__":
    out_file = generate_report()
