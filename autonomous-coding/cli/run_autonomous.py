#!/usr/bin/env python3
"""
Autonomous Coding Agent Runner (CLI Version)
=============================================

Entry point for running the autonomous coding agent using Claude Code CLI.

Usage:
    python run_autonomous.py --project-dir /path/to/project
    python run_autonomous.py --project-dir /path/to/project --max-iterations 5
    python run_autonomous.py --project-dir /path/to/project --model claude-sonnet-4-5-20250929
"""

import argparse
from pathlib import Path

from orchestrator import run_autonomous_agent


DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


def main():
    parser = argparse.ArgumentParser(
        description="Run the autonomous coding agent using Claude Code CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start a new project
    python run_autonomous.py --project-dir ./my-app

    # Continue with limited iterations
    python run_autonomous.py --project-dir ./my-app --max-iterations 5

    # Use a specific model
    python run_autonomous.py --project-dir ./my-app --model claude-opus-4-20250514
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        required=True,
        help="Directory for the project (required)",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent sessions (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )

    args = parser.parse_args()

    # Resolve project directory to absolute path
    project_dir = args.project_dir.resolve()

    # Run the agent
    run_autonomous_agent(
        project_dir=project_dir,
        model=args.model,
        max_iterations=args.max_iterations,
    )


if __name__ == "__main__":
    main()
