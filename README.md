<<<<<<< HEAD
# BreakBot

BreakBot is an AI red-team agent that analyzes codebases, generates adversarial pytest cases, runs them in a sandboxed subprocess, and produces structured Bug Attack Reports in Markdown and JSON.

It accepts a public GitHub repository URL or pasted code, uses Google Gemini to reason about functions and weak points, generates hostile edge-case tests, runs them with pytest, and asks the LLM for fix suggestions for failed attacks.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11+ |
| LLM | Google Gemini API, `gemini-1.5-flash` |
| UI | Streamlit |
| Repo ingestion | GitHub REST API and raw.githubusercontent.com |
| Test runner | Python `subprocess` + pytest |
| Reports | Markdown + JSON |
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
streamlit run app.py
```

## Example Use Case

1. Open the Streamlit app.
2. Choose `Paste Code`.
3. Paste a fragile function such as:

```python
def divide(a, b):
    return a / b
```

4. Click `Analyze Code`.
5. Review weak points.
6. Click `⚔️ Launch Attack`.
7. Click `🧪 Run Tests`.
8. Download the Bug Attack Report from the UI.

Reports are saved automatically:

```text
reports/{repo_name}_{timestamp}.md
reports/{repo_name}_{timestamp}.json
```

## Architecture

```text
                +----------------------+
                |   Streamlit app.py   |
                +----------+-----------+
                           |
             +-------------+-------------+
             |                           |
  +----------v----------+     +----------v----------+
  | GitHub Repo Input   |     | Pasted Code Input   |
  +----------+----------+     +----------+----------+
             |                           |
             +-------------+-------------+
                           |
                  +--------v--------+
                  | agent/ingester  |
                  +--------+--------+
                           |
                  +--------v--------+
                  | agent/analyzer  |---- Gemini ANALYZE_PROMPT
                  +--------+--------+
                           |
                  +--------v--------+
                  | agent/attacker  |---- Gemini ATTACK_GEN_PROMPT
                  +--------+--------+
                           |
                  +--------v--------+
                  | agent/runner    |---- pytest subprocess
                  +--------+--------+
                           |
                  +--------v--------+
                  | agent/reporter  |---- Gemini FIX_SUGGEST_PROMPT
                  +--------+--------+
                           |
             +-------------v-------------+
             | reports/*.md + reports/*.json |
             +---------------------------+
```

## Project Structure

```text
agent/
  analyzer.py          # Gemini JSON analysis with chunking and fallback
  attacker.py          # Adversarial pytest generation
  llm_client.py        # Gemini client using .env
  fixer.py             # Single-fix compatibility helper
  ingester.py          # GitHub and pasted-code ingestion
  reporter.py          # Markdown/JSON reports and fix suggestions
  runner.py            # Sandboxed subprocess pytest runner
utils/
  prompt_templates.py  # LLM prompt constants
app.py                 # Dark-themed Streamlit workflow
requirements.txt       # Runtime and dev dependencies
```

## Safety

BreakBot runs generated tests in a subprocess, and it never uses `exec()` or `eval()` to execute generated test code. A subprocess is not a full security sandbox, so run BreakBot in a disposable environment or container when testing unknown repositories.
=======
# BreakBot
>>>>>>> 21d6e42691b35b1db81d4cf60b5687f148d9a0b0
