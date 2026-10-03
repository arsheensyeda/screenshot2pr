import os
import re
import json
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemma-4-26b-a4b-it"  # if it is slow or errors, try "gemma-4-26b-a4b-it"
MAX_RULES_CHARS = 3000
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
CANDIDATES = [
    "CONTRIBUTING.md",
    ".github/CONTRIBUTING.md",
    "docs/CONTRIBUTING.md",
    "CONTRIBUTING.rst",
    "contributing.md",
]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

with open("system_prompt.txt", encoding="utf-8") as f:
    PROMPT_TEMPLATE = f.read()

# Shown only if the AI call fails twice, and clearly labeled as a saved demo.
FALLBACK = {
    "is_error": True,
    "error_type": "NameError",
    "summary": "A Python script crashed with a NameError: 'undefined_variable' is used before it is defined.",
    "likely_cause": "The variable was never assigned, or its name is misspelled.",
    "confidence": "high",
    "where_to_look": ["The file and line shown in the traceback (line 1 of bad.py)"],
    "issue": {
        "title": "NameError: name 'undefined_variable' is not defined",
        "body": "**What happened**\nRunning the script raised a NameError.\n\n**Steps to reproduce**\nPlease fill in.\n\n**Expected**\nThe script runs.\n\n**Actual**\n`NameError: name 'undefined_variable' is not defined`",
    },
    "pr_checklist": [
        {"step": "Comment on the issue to get it assigned before starting", "source": "general"},
        {"step": "Create a new branch for your change", "source": "general"},
        {"step": "Run the project's tests before pushing", "source": "general"},
        {"step": "Open a pull request and describe what you changed", "source": "general"},
    ],
}


def parse_repo(url):
    m = re.match(r"https?://github\.com/([^/\s]+)/([^/\s#?]+)", url.strip())
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def fetch_contributing(owner, repo):
    for path in CANDIDATES:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
        try:
            r = requests.get(url, timeout=8)
        except requests.RequestException:
            continue
        if r.status_code == 200 and r.text.strip():
            return r.text[:MAX_RULES_CHARS], path
    return "", ""


def call_gemma(image_bytes, mime, prompt):
    resp = client.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime), prompt],
    )
    return resp.text


def parse_json(text):
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object in reply")
    return json.loads(text[start:end + 1])


def normalize(d, rules_found):
    issue = d.get("issue") or {}
    checklist = []
    for item in d.get("pr_checklist") or []:
        if isinstance(item, dict):
            step = str(item.get("step", "")).strip()
            from_rules = rules_found and item.get("source") == "contributing"
            source = "contributing" if from_rules else "general"
        else:
            step, source = str(item).strip(), "general"
        if step:
            checklist.append({"step": step, "source": source})
    return {
        "is_error": bool(d.get("is_error", True)),
        "error_type": str(d.get("error_type", "")),
        "summary": str(d.get("summary", "")),
        "likely_cause": str(d.get("likely_cause", "")),
        "confidence": str(d.get("confidence", "")),
        "where_to_look": [str(x) for x in (d.get("where_to_look") or [])],
        "issue": {"title": str(issue.get("title", "")), "body": str(issue.get("body", ""))},
        "pr_checklist": checklist,
    }


@app.route("/")
def home():
    return render_template("analyzer.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    image = request.files.get("image")
    repo_url = request.form.get("repo_url", "").strip()

    if not image or image.filename == "":
        return jsonify({"error": "Please choose a screenshot first."}), 400
    if image.mimetype not in ALLOWED_TYPES:
        return jsonify({"error": "Please upload a PNG, JPG or WEBP image."}), 400

    image_bytes = image.read()

    rules, rules_source, repo_label, repo_status = "", "", "", "none"
    if repo_url:
        parsed = parse_repo(repo_url)
        if not parsed:
            repo_status = "invalid"
        else:
            owner, repo = parsed
            repo_label = f"{owner}/{repo}"
            rules, rules_source = fetch_contributing(owner, repo)
            repo_status = "ok" if rules else "no_file"

    prompt = PROMPT_TEMPLATE.replace("{{REPO_RULES}}", rules if rules else "(none provided)")

    data, raw = None, None
    for _ in range(2):
        try:
            raw = call_gemma(image_bytes, image.mimetype, prompt)
            data = parse_json(raw)
            break
        except Exception as e:
            print("Gemma error:", e, "| raw reply:", raw)

    offline = data is None
    if offline:
        data = dict(FALLBACK)

    result = normalize(data, bool(rules))
    result.update({
        "offline_demo": offline,
        "repo": repo_label,
        "repo_status": repo_status,
        "rules_source": rules_source,
    })
    return jsonify(result)


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "That image is too large. Please keep it under 8 MB."}), 413


if __name__ == "__main__":
    app.run(debug=True)