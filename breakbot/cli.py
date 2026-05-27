from __future__ import annotations

import argparse
import json

from breakbot.agent import BreakBotAgent
from breakbot.config import BreakBotConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BreakBot from the command line.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--github-url", help="Public GitHub repository URL")
    source.add_argument("--code", help="Pasted Python code")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    parser.add_argument("--no-run", action="store_true", help="Generate tests without running pytest")
    args = parser.parse_args()

    report = BreakBotAgent(BreakBotConfig()).attack(
        github_url=args.github_url,
        pasted_code=args.code,
        run_tests=not args.no_run,
    )
    if args.json:
        print(json.dumps(report.to_json(), indent=2))
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    main()
