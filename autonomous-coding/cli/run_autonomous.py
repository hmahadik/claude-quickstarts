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

    # Start a new project with description and non-interactive spec generation
    python run_autonomous.py --project-dir ./my-app --description "Build a claude.ai clone" --non-interactive

    # Audit an existing project to generate a prescriptive spec
    python run_autonomous.py --project-dir ./existing-app --audit

    # Generate more or fewer features (default: 10)
    python run_autonomous.py --project-dir ./my-app --feature-count 25

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

    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Project description for spec generation (avoids interactive prompt)",
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (generates spec automatically without interview)",
    )

    parser.add_argument(
        "--audit",
        action="store_true",
        help="Audit existing codebase to generate a prescriptive spec (what it SHOULD do, not just what it does)",
    )

    parser.add_argument(
        "--feature-count",
        type=int,
        default=10,
        help="Number of features/tests to generate in feature_list.json (default: 10)",
    )

    args = parser.parse_args()

    # Resolve project directory to absolute path
    project_dir = args.project_dir.resolve()

    # Run the agent
    run_autonomous_agent(
        project_dir=project_dir,
        model=args.model,
        max_iterations=args.max_iterations,
        description=args.description,
        non_interactive=args.non_interactive,
        audit=args.audit,
        feature_count=args.feature_count,
    )


if __name__ == "__main__":
    main()
