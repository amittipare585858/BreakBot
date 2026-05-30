# BreakBot

BreakBot is a full-stack AI red-team web application that analyzes code, generates adversarial pytest cases, runs them through the local test pipeline, and produces bug attack reports with fix suggestions.

The rebuilt app uses a FastAPI backend in `api.py` and a pure HTML/CSS/JS frontend in `index.html`. It does not depend on Streamlit.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11+ and FastAPI |
| Frontend | Plain HTML, CSS, and JavaScript |
| LLM | Google Gemini API |
| Repo ingestion | GitHub REST API and raw.githubusercontent.com |
| Test runner | Python subprocess and pytest |
| Reports | Markdown and JSON |
| Config | `.env` via `python-dotenv` |

## Setup

```powershell
cd D:\BreakBot_Complete
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_key_here
```

## Run

```powershell
uvicorn api:app --reload
```

Open the app at:

```text
http://127.0.0.1:8000
```

## Example Use Case

1. Open the FastAPI-served web app.
2. Choose `Paste Code`.
3. Paste a fragile function such as:

```python
def divide(a, b):
    return a / b
```

4. Click `Analyze`.
5. Review weak points.
6. Click `Generate Attack`.
7. Click `Run Full Report`.
8. Review the Bug Attack Report in the UI.

Reports are saved automatically:

```text
reports/{repo_name}_{timestamp}.md
reports/{repo_name}_{timestamp}.json
```

## Architecture

```text
                +--------------------------+
                | FastAPI api.py + index.html |
                +------------+-------------+
                             |
             +---------------+---------------+
             |                               |
  +----------v----------+         +----------v----------+
  | GitHub Repo Input   |         | Pasted Code Input   |
  +----------+----------+         +----------+----------+
             |                               |
             +---------------+---------------+
                             |
                    +--------v--------+
                    | agent/ingester  |
                    +--------+--------+
                             |
                    +--------v--------+
                    | agent/analyzer  |
                    +--------+--------+
                             |
                    +--------v--------+
                    | agent/attacker  |
                    +--------+--------+
                             |
                    +--------v--------+
                    | agent/runner    |
                    +--------+--------+
                             |
                    +--------v--------+
                    | agent/reporter  |
                    +--------+--------+
                             |
               +-------------v-------------+
               | reports/*.md + reports/*.json |
               +---------------------------+
```

## Project Structure

```text
agent/
  analyzer.py          # Gemini JSON analysis with fallback parsing
  attacker.py          # Adversarial pytest generation
  fix_suggester.py     # Fix suggestion generation
  ingester.py          # GitHub repository ingestion
  reporter.py          # Markdown/JSON reports
  runner.py            # Subprocess pytest runner
api.py                 # FastAPI backend
index.html             # Pure HTML/CSS/JS frontend
requirements.txt       # Runtime and dev dependencies
```

## Safety

BreakBot runs generated tests in a subprocess, and it never uses `exec()` or `eval()` to execute generated test code. A subprocess is not a full security sandbox, so run BreakBot in a disposable environment or container when testing unknown repositories.
