# screenshot2pr
Turn a screenshot of an error into a ready-to-paste GitHub issue and a first-PR checklist, based on the target repo's own contributing rules.


Built at Hacktoberfest Hack Day Hyderabad (MLH × DEV × React Hyderabad) for the Best Use of Gemma 4 and Best Open-Source AI Project challenges.

<img width="1856" height="1504" alt="Screenshot 2026-10-03 124339" src="https://github.com/user-attachments/assets/25bb2c04-e9b8-4562-85ce-a08b5becdbb6" />



<img width="1712" height="1794" alt="Screenshot 2026-10-03 124401" src="https://github.com/user-attachments/assets/234d5192-2fde-4eb4-9844-dc71b8d0e89a" />



<img width="1718" height="1800" alt="Screenshot 2026-10-03 124434" src="https://github.com/user-attachments/assets/1d67a16a-a2f9-4b19-a67e-9cf58d80af82" />








The problem

Open-source contributors often get stuck on an error and then don't know how to report it, or what a project expects before they open a pull request. Error text in a terminal is also awkward to copy, so people end up describing it badly or not reporting it at all.

What it does
You upload (or paste with Ctrl + V) a screenshot of an error, and optionally a GitHub repo URL.
The app fetches the repo's CONTRIBUTING file from GitHub.
Gemma 4 reads the screenshot together with those rules.
You get:
a plain-language explanation of the error and its likely cause
where to look next
a ready-to-paste GitHub issue (with a Copy button)
a first-PR checklist, where each step is labeled from CONTRIBUTING (stated in the repo's own rules) or general (common practice)

The labels matter: a step is only marked "from CONTRIBUTING" if the repo's rules text was found and the model attributed the step to it. If no rules are found, every step is shown as general advice, and the page says so.

Why Gemma 4

Gemma 4 is an open-weight multimodal model. It reads the screenshot directly, so users don't have to retype error text, and the model is central to the workflow: without it, there is no product. This project uses gemma-4-26b-a4b-it, called through the Gemini API (see app.py).

How it works
Screenshot + repo URL
        │
        ├─► GitHub raw files ─► CONTRIBUTING text (first ~3000 characters)
        │
        ▼
 Gemma 4 (Gemini API) ─► structured JSON
        │
        ▼
 Flask backend (validates and normalizes) ─► results page
The prompt in system_prompt.txt tells the model to answer with one JSON object, to never invent rules, and to ignore instructions hidden inside screenshots or repo files.
The backend extracts and validates the JSON, retries once if parsing fails, and forces every checklist item to "general" when no rules were found.
If the AI call fails twice, the page shows a saved demo result under a clear warning banner, so it never silently passes off fake output as an analysis.
Handled cases
Screenshot is not an error: friendly message instead of made-up output
Invalid GitHub URL, or a repo with no CONTRIBUTING file: the screenshot is still analyzed, and the checklist falls back to general advice
Wrong file type or an image over 8 MB: rejected with a clear message
API failure: labeled fallback result
Setup
bash
git clone https://github.com/arsheensyeda/screenshot2pr
cd screenshot2pr
python -m venv venv
# Windows: venv\Scripts\activate    Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

Create a .env file in the project folder:

GEMINI_API_KEY=your_key_here

Get a key at Google AI Studio. Then run:

bash
python app.py

Open http://127.0.0.1:5000.

Try it

Sample error screenshots are in the samples/ folder. Upload one and paste a repo URL, for example https://github.com/python/mypy.

Note: analysis can take 20 to 60 seconds, because the model reads the image.

Project structure
app.py               Flask backend: fetch rules, call Gemma 4, validate output
system_prompt.txt    Prompt and output format sent to Gemma 4
templates/
  analyzer.html      Upload page and results UI
samples/             Example error screenshots
test.py              Small script to check your API key and model name
requirements.txt     Python dependencies
Limitations
Only the first ~3000 characters of the CONTRIBUTING file are read.
It looks for the file at a few common locations (CONTRIBUTING.md, .github/CONTRIBUTING.md, docs/CONTRIBUTING.md, CONTRIBUTING.rst).
Model output can be wrong. Always check the suggested cause and steps before filing an issue.
Built in a two-hour hackathon, so this is a prototype.
Ideas for next steps
Read more repo files, such as the pull request template
Search the repo to point at the exact file the error comes from
Support pasted error text and logs alongside screenshots
Tech stack

Python, Flask, Gemma 4 (gemma-4-26b-a4b-it) via the Gemini API (google-genai), requests, HTML and JavaScript.

License

MIT, see LICENSE.

Author

Built by Arsheen (@arsheensyeda).
