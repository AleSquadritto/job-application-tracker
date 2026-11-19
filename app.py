"""Job Application Tracker - Flask application.

Pages: dashboard, CRUD for companies / jobs / applications / contacts, and Job Match.
"""
import json
import os
import re
from datetime import date, datetime

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from markupsafe import escape

from database import execute, parse_json, query

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# Entity configuration (one place that describes every table and its form)
def field(name, label, kind="text", required=False, maxlen=None, choices=None, fk=None, hint=None):
    return {"name": name, "label": label, "kind": kind, "required": required,
            "maxlen": maxlen, "choices": choices, "fk": fk, "hint": hint}


ENTITIES = {
    "companies": {
        "table": "companies", "pk": "company_id", "alias": "c",
        "singular": "Company", "title": "Companies",
        "base_sql": """SELECT c.*, (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id) AS job_count
                       FROM companies c""",
        "order": "c.company_name",
        "delete_msg": "Delete this company? Its jobs, applications and contacts will be deleted too.",
        "fields": [
            field("company_name", "Company name", required=True, maxlen=100),
            field("industry", "Industry", maxlen=50),
            field("website", "Website", "url", maxlen=200),
            field("city", "City", maxlen=50),
            field("state", "State", maxlen=50),
            field("notes", "Notes", "textarea"),
        ],
    },
    "jobs": {
        "table": "jobs", "pk": "job_id", "alias": "j",
        "singular": "Job", "title": "Jobs",
        "base_sql": """SELECT j.*, c.company_name FROM jobs j
                       JOIN companies c ON c.company_id = j.company_id""",
        "order": "j.date_posted DESC, j.job_id DESC",
        "delete_msg": "Delete this job? Its applications will be deleted too.",
        "fields": [
            field("company_id", "Company", "select", required=True, fk="companies"),
            field("job_title", "Job title", required=True, maxlen=100),
            field("job_type", "Job type", "select", choices=JOB_TYPES),
            field("salary_min", "Minimum salary ($)", "int"),
            field("salary_max", "Maximum salary ($)", "int"),
            field("job_url", "Job URL", "url", maxlen=300),
            field("date_posted", "Date posted", "date"),
        ],
        "json_col": "requirements", "json_title": "Requirements (stored in a JSON column)",
        "json_fields": [
            field("j_required_skills", "Required skills", "list", hint="Comma-separated, e.g. Python, SQL, Flask"),
            field("j_preferred_skills", "Preferred skills", "list", hint="Comma-separated"),
            field("j_education", "Education", maxlen=100),
            field("j_experience_years", "Years of experience", "int"),
            field("j_remote_option", "Remote option", "bool"),
        ],
    },
    "applications": {
        "table": "applications", "pk": "application_id", "alias": "a",
        "singular": "Application", "title": "Applications",
        "base_sql": """SELECT a.*, j.job_title, c.company_name FROM applications a
                       JOIN jobs j ON j.job_id = a.job_id
                       JOIN companies c ON c.company_id = j.company_id""",
        "order": "a.application_date DESC, a.application_id DESC",
        "delete_msg": "Delete this application?",
        "fields": [
            field("job_id", "Job", "select", required=True, fk="jobs"),
            field("application_date", "Application date", "date", required=True),
            field("status", "Status", "select", required=True, choices=STATUSES),
            field("resume_version", "Resume version", maxlen=50),
            field("cover_letter_sent", "Cover letter sent", "bool"),
        ],
        "json_col": "interview_data", "json_title": "Interview details (stored in a JSON column)",
        "json_fields": [
            field("j_interview_rounds", "Interview rounds", "int"),
            field("j_interviewers", "Interviewers", "list", hint="Comma-separated names"),
            field("j_technical_questions", "Technical questions", "list", hint="Comma-separated"),
            field("j_feedback", "Feedback", "textarea"),
            field("j_next_steps", "Next steps", maxlen=200),
        ],
    },
    "contacts": {
        "table": "contacts", "pk": "contact_id", "alias": "ct",
        "singular": "Contact", "title": "Contacts",
        "base_sql": """SELECT ct.*, c.company_name FROM contacts ct
                       JOIN companies c ON c.company_id = ct.company_id""",
        "order": "ct.contact_name",
        "delete_msg": "Delete this contact?",
        "fields": [
            field("company_id", "Company", "select", required=True, fk="companies"),
            field("contact_name", "Contact name", required=True, maxlen=100),
            field("title", "Title", maxlen=100),
            field("email", "Email", "email", maxlen=100),
            field("phone", "Phone", maxlen=20),
            field("linkedin_url", "LinkedIn URL", "url", maxlen=200),
            field("notes", "Notes", "textarea"),
        ],
    },
}

def get_cfg(entity):
    if entity not in ENTITIES:
        abort(404)
    return ENTITIES[entity]


# Helpers: foreign-key dropdowns, validation, JSON packing, saving
def fk_options(target):
    """Dropdown options (id, label) for a foreign key pointing at `target`."""
    if target == "companies":
        rows = query("SELECT company_id AS id, company_name AS label FROM companies ORDER BY company_name")
    else:
        rows = query("""SELECT j.job_id AS id, CONCAT(j.job_title, ' @ ', c.company_name) AS label
                        FROM jobs j JOIN companies c ON c.company_id = j.company_id
                        ORDER BY c.company_name, j.job_title""")
    return [(r["id"], r["label"]) for r in rows]


def with_options(fields):
    """Copy field definitions and attach dropdown options to select fields."""
    result = []
    for f in fields:
        f = dict(f)
        if f["kind"] == "select":
            f["options"] = fk_options(f["fk"]) if f["fk"] else [(c, c) for c in f["choices"]]
        result.append(f)
    return result


def clean_value(f, raw):
    """Validate one submitted value. Returns (value, error_message)."""
    kind, label = f["kind"], f["label"]
    if kind == "bool":
        return bool(raw), None
    raw = (raw or "").strip()
    if raw == "":
        return (None, f"{label} is required.") if f["required"] else (None, None)
    if f["maxlen"] and len(raw) > f["maxlen"]:
        return None, f"{label} must be at most {f['maxlen']} characters."
    if kind == "int":
        if not raw.isdigit() or int(raw) > 2_000_000_000:
            return None, f"{label} must be a whole number (0 or more)."
        return int(raw), None
    if kind == "date":
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date(), None
        except ValueError:
            return None, f"{label} must be a valid date."
    if kind == "select":
        valid = {str(value): value for value, _ in f["options"]}
        if raw not in valid:
            return None, f"Choose a valid {label.lower()}."
        return valid[raw], None
    if kind == "email" and not EMAIL_RE.match(raw):
        return None, "Enter a valid email address."
    if kind == "url" and not raw.lower().startswith(("http://", "https://")):
        return None, f"{label} must start with http:// or https://"
    if kind == "list":
        return [item.strip() for item in raw.split(",") if item.strip()], None
    return raw, None


def validate(cfg, form):
    """Validate a submitted form. Returns (values, errors) keyed by field name."""
    values, errors = {}, {}
    for f in with_options(cfg["fields"] + cfg.get("json_fields", [])):
        value, error = clean_value(f, form.get(f["name"]))
        values[f["name"]] = value
        if error:
            errors[f["name"]] = error
    low, high = values.get("salary_min"), values.get("salary_max")
    if low is not None and high is not None and low > high:
        errors["salary_max"] = "Maximum salary must be at least the minimum salary."
    return values, errors


def save(cfg, values, record_id=None):
    """INSERT or UPDATE a record. Column names come from our config, never from user input."""
    columns = {f["name"]: values[f["name"]] for f in cfg["fields"]}
    if cfg.get("json_col"):
        doc = {}
        if record_id:  # keep keys the form doesn't edit (e.g. offer_amount)
            row = query(f"SELECT {cfg['json_col']} AS doc FROM {cfg['table']} WHERE {cfg['pk']} = %s",
                        (record_id,), one=True)
            doc = parse_json(row["doc"]) if row else {}
            doc = doc if isinstance(doc, dict) else {}
        for f in cfg["json_fields"]:
            value, key = values[f["name"]], f["name"][2:]
            if value in (None, [], ""):
                doc.pop(key, None)
            else:
                doc[key] = value
        columns[cfg["json_col"]] = json.dumps(doc) if doc else None

    names = list(columns)
    params = [columns[n] for n in names]
    if record_id:
        assignments = ", ".join(f"{n} = %s" for n in names)
        execute(f"UPDATE {cfg['table']} SET {assignments} WHERE {cfg['pk']} = %s", params + [record_id])
        return record_id
    marks = ", ".join(["%s"] * len(names))
    return execute(f"INSERT INTO {cfg['table']} ({', '.join(names)}) VALUES ({marks})", params)


def row_to_form_values(cfg, row):
    """Convert a database row into the string values an edit form expects."""
    values = {}
    for f in cfg["fields"]:
        v = row[f["name"]]
        values[f["name"]] = bool(v) if f["kind"] == "bool" else ("" if v is None else str(v))
    doc = parse_json(row.get(cfg.get("json_col"))) if cfg.get("json_col") else None
    doc = doc if isinstance(doc, dict) else {}
    for f in cfg.get("json_fields", []):
        v = doc.get(f["name"][2:])
        if f["kind"] == "bool":
            values[f["name"]] = bool(v)
        elif isinstance(v, list):
            values[f["name"]] = ", ".join(str(x) for x in v)
        else:
            values[f["name"]] = "" if v is None else str(v)
    return values


def json_details(cfg, row):
    """(label, value) pairs describing a record's JSON column, including extra keys."""
    doc = parse_json(row.get(cfg.get("json_col"))) if cfg.get("json_col") else None
    if not isinstance(doc, dict):
        return []
    known = {f["name"][2:]: f["label"] for f in cfg["json_fields"]}
    details = []
    for key, value in doc.items():
        label = known.get(key, key.replace("_", " ").capitalize())
        if isinstance(value, list):
            value = ", ".join(str(x) for x in value)
        elif isinstance(value, bool):
            value = "Yes" if value else "No"
        details.append((label, value))
    return details


@app.template_filter("salary")
def salary_filter(row):
    low, high = row.get("salary_min"), row.get("salary_max")
    if low is None and high is None:
        return "—"
    if low is not None and high is not None:
        return f"${low:,} – ${high:,}"
    return f"${(low if low is not None else high):,}"


# Dashboard
@app.route("/")
def dashboard():
    counts = {t: query(f"SELECT COUNT(*) AS n FROM {t}", one=True)["n"]
              for t in ("companies", "jobs", "applications", "contacts")}
    by_status = {s: 0 for s in STATUSES}
    for r in query("SELECT status, COUNT(*) AS n FROM applications GROUP BY status"):
        by_status[r["status"]] = r["n"]
    total = counts["applications"]
    responses = total - by_status["Applied"]
    response_rate = round(100 * responses / total) if total else 0
    pay = query("SELECT ROUND(AVG(salary_min)) AS low, ROUND(AVG(salary_max)) AS high FROM jobs", one=True)
    recent = query(ENTITIES["applications"]["base_sql"] + " ORDER BY " + ENTITIES["applications"]["order"] + " LIMIT 5")
    return render_template("dashboard.html", counts=counts, by_status=by_status, total=total,
                           response_rate=response_rate, pay=pay, recent=recent)



# CRUD routes for all four tables
@app.route("/<entity>/")
def list_view(entity):
    cfg = get_cfg(entity)
    rows = query(f"{cfg['base_sql']} ORDER BY {cfg['order']}")
    return render_template(f"{entity}.html", mode="list", rows=rows, entity=entity, cfg=cfg)


@app.route("/<entity>/<int:rid>")
def detail_view(entity, rid):
    cfg = get_cfg(entity)
    row = query(f"{cfg['base_sql']} WHERE {cfg['alias']}.{cfg['pk']} = %s", (rid,), one=True)
    if not row:
        abort(404)
    related = []
    if entity == "companies":
        related.append(("Jobs", [(f"{r['job_title']} ({r['job_type'] or 'n/a'})", url_for("detail_view", entity="jobs", rid=r["job_id"]))
                                 for r in query("SELECT job_id, job_title, job_type FROM jobs WHERE company_id = %s", (rid,))],
                        url_for("new_view", entity="jobs", company_id=rid), "Add job"))
        related.append(("Contacts", [(f"{r['contact_name']} - {r['title'] or 'n/a'}", url_for("detail_view", entity="contacts", rid=r["contact_id"]))
                                     for r in query("SELECT contact_id, contact_name, title FROM contacts WHERE company_id = %s", (rid,))],
                        url_for("new_view", entity="contacts", company_id=rid), "Add contact"))
    elif entity == "jobs":
        related.append(("Applications", [(f"{r['application_date']} - {r['status']}", url_for("detail_view", entity="applications", rid=r["application_id"]))
                                         for r in query("SELECT application_id, application_date, status FROM applications WHERE job_id = %s", (rid,))],
                        url_for("new_view", entity="applications", job_id=rid), "Add application"))
    return render_template(f"{entity}.html", mode="detail", entity=entity, cfg=cfg, row=row,
                           fields=cfg["fields"], json_info=json_details(cfg, row), related=related)


def render_form(entity, cfg, values, errors, record_id=None):
    return render_template(f"{entity}.html", mode="form", entity=entity, cfg=cfg, values=values, errors=errors,
                           fields=with_options(cfg["fields"]), json_fields=with_options(cfg.get("json_fields", [])),
                           record_id=record_id)


@app.route("/<entity>/new", methods=["GET", "POST"])
def new_view(entity):
    cfg = get_cfg(entity)
    if request.method == "POST":
        values, errors = validate(cfg, request.form)
        if not errors:
            rid = save(cfg, values)
            flash(f"{cfg['singular']} added.", "success")
            return redirect(url_for("detail_view", entity=entity, rid=rid))
        flash("Please fix the errors below.", "error")
        return render_form(entity, cfg, request.form.to_dict(), errors)
    defaults = {f["name"]: request.args.get(f["name"], "") for f in cfg["fields"]}  # e.g. ?company_id=3
    if entity == "applications":
        defaults["application_date"] = defaults["application_date"] or date.today().isoformat()
        defaults["status"] = defaults["status"] or "Applied"
    return render_form(entity, cfg, defaults, {})


@app.route("/<entity>/<int:rid>/edit", methods=["GET", "POST"])
def edit_view(entity, rid):
    cfg = get_cfg(entity)
    row = query(f"{cfg['base_sql']} WHERE {cfg['alias']}.{cfg['pk']} = %s", (rid,), one=True)
    if not row:
        abort(404)
    if request.method == "POST":
        values, errors = validate(cfg, request.form)
        if not errors:
            save(cfg, values, rid)
            flash(f"{cfg['singular']} updated.", "success")
            return redirect(url_for("detail_view", entity=entity, rid=rid))
        flash("Please fix the errors below.", "error")
        return render_form(entity, cfg, request.form.to_dict(), errors, rid)
    return render_form(entity, cfg, row_to_form_values(cfg, row), {}, rid)


@app.route("/<entity>/<int:rid>/delete", methods=["POST"])
def delete_view(entity, rid):
    cfg = get_cfg(entity)
    if not query(f"SELECT 1 AS found FROM {cfg['table']} WHERE {cfg['pk']} = %s", (rid,), one=True):
        abort(404)
    execute(f"DELETE FROM {cfg['table']} WHERE {cfg['pk']} = %s", (rid,))
    flash(f"{cfg['singular']} deleted.", "success")
    return redirect(url_for("list_view", entity=entity))


# Job Match: rank jobs by how many required skills the user has
def normalize(skill):
    return re.sub(r"\s+", " ", str(skill).strip().lower())


def match_jobs(user_skills):
    """Return (results, skipped). Each result has percent, matched and missing skills."""
    have = {normalize(s) for s in user_skills if str(s).strip()}
    results, skipped = [], 0
    jobs = query("""SELECT j.job_id, j.job_title, j.requirements, c.company_name
                    FROM jobs j JOIN companies c ON c.company_id = j.company_id""")
    for job in jobs:
        doc = parse_json(job["requirements"])
        required = doc.get("required_skills") if isinstance(doc, dict) else None
        if not required:
            skipped += 1  # nothing to compare against
            continue
        required = list(dict.fromkeys(str(s).strip() for s in required))
        matched = [s for s in required if normalize(s) in have]
        missing = [s for s in required if normalize(s) not in have]
        results.append({
            "job_id": job["job_id"], "job_title": job["job_title"], "company_name": job["company_name"],
            "matched": matched, "missing": missing, "total": len(required),
            "percent": round(100 * len(matched) / len(required)),
        })
    results.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["job_title"].lower()))
    return results, skipped


@app.route("/job-match")
def job_match():
    skills_text = request.args.get("skills", "").strip()
    user_skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    results, skipped = match_jobs(user_skills) if user_skills else ([], 0)
    known = set()
    for row in query("SELECT requirements FROM jobs"):
        doc = parse_json(row["requirements"])
        if isinstance(doc, dict):
            known.update(str(s) for s in doc.get("required_skills", []) + doc.get("preferred_skills", []))
    return render_template("job_match.html", skills_text=skills_text, user_skills=user_skills,
                           results=results, skipped=skipped, known_skills=sorted(known, key=str.lower))


@app.errorhandler(mysql.connector.Error)
def database_error(error):
    return (f"<h1>Database error</h1><p>{escape(str(error))}</p>"
            "<p>Check that MySQL is running, schema.sql has been loaded, and the DB_HOST, DB_USER, "
            "DB_PASSWORD and DB_NAME environment variables are correct.</p>"), 500


if __name__ == "__main__":
    # Port 5001: on macOS, port 5000 is often taken by AirPlay Receiver.
    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))