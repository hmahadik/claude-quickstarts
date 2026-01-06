"""
Orchestrator - CLI Session Management
=====================================

Manages autonomous coding sessions using the Claude Code CLI.
Replaces the SDK-based agent.py and client.py with subprocess calls to `claude`.
"""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from progress import print_session_header, print_progress_summary
from prompts import get_initializer_prompt, get_coding_prompt, get_spec_generator_prompt


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3
CLI_HARNESS_DIR = Path(__file__).parent


def setup_project(project_dir: Path) -> None:
    """
    Set up the .claude/ directory in the project with hooks and settings.

    Copies the hooks and settings from the cli/.claude directory to enable
    security validation in the target project.
    """
    source_claude_dir = CLI_HARNESS_DIR / ".claude"
    dest_claude_dir = project_dir / ".claude"

    # Create .claude directory
    dest_claude_dir.mkdir(parents=True, exist_ok=True)

    # Copy settings.json
    settings_source = source_claude_dir / "settings.json"
    settings_dest = dest_claude_dir / "settings.json"
    if settings_source.exists():
        shutil.copy(settings_source, settings_dest)

    # Copy hooks directory
    hooks_source = source_claude_dir / "hooks"
    hooks_dest = dest_claude_dir / "hooks"
    if hooks_source.exists():
        if hooks_dest.exists():
            shutil.rmtree(hooks_dest)
        shutil.copytree(hooks_source, hooks_dest)

        # Ensure hook script is executable
        hook_script = hooks_dest / "validate-bash.py"
        if hook_script.exists():
            hook_script.chmod(0o755)

    print(f"Set up .claude/ directory in {project_dir}")


def run_interactive_spec_generation(
    project_dir: Path,
    description: str,
    model: str,
) -> bool:
    """
    Run an interactive Claude session to generate the app specification.

    The user will have a conversation with Claude to flesh out requirements.
    Claude will write app_spec.txt when enough information is gathered.

    Args:
        project_dir: Directory for the project
        description: User's high-level description of what to build
        model: Model to use

    Returns:
        True if app_spec.txt was created, False otherwise
    """
    print("\n" + "=" * 70)
    print("  SPEC GENERATION (Interactive)")
    print("=" * 70)
    print("\nClaude will interview you to understand your requirements.")
    print("Once the spec is generated, exit the session (Ctrl+C or /exit).")
    print("-" * 70 + "\n")

    system_prompt = get_spec_generator_prompt(description)

    cmd = [
        "claude",
        "--system-prompt", system_prompt,
        "--model", model,
    ]

    try:
        # Run interactively (no -p flag, no capture)
        subprocess.run(cmd, cwd=project_dir)
    except KeyboardInterrupt:
        print("\n\nSpec generation session ended.")
    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Ensure Claude Code is installed.")
        return False

    # Check if spec was created
    spec_file = project_dir / "app_spec.txt"
    if spec_file.exists():
        print("\n" + "=" * 70)
        print("  app_spec.txt created successfully!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("  Warning: app_spec.txt was not created.")
        print("  Run again to retry spec generation.")
        print("=" * 70)
        return False


def run_cli_session(
    project_dir: Path,
    prompt: str,
    model: str,
) -> tuple[str, int]:
    """
    Run a single Claude CLI session.

    Args:
        project_dir: Directory to run in (cwd)
        prompt: The prompt to send to Claude
        model: Model to use

    Returns:
        (output, return_code) tuple
    """
    cmd = [
        "claude",
        "-p", prompt,
        "--model", model,
    ]

    print(f"Running: claude -p '...' --model {model}")
    print(f"Working directory: {project_dir}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=False,  # Let output stream to terminal
            text=True,
        )
        return "", result.returncode
    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Ensure Claude Code is installed.")
        return "claude CLI not found", 1
    except Exception as e:
        return str(e), 1


def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Run the autonomous agent loop using Claude CLI.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
    """
    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT (CLI VERSION)")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Set up .claude/ directory with hooks and settings
    setup_project(project_dir)

    # Step 1: Check if app_spec.txt exists - if not, run spec generation
    spec_file = project_dir / "app_spec.txt"
    if not spec_file.exists():
        print("\n" + "-" * 70)
        print("No app_spec.txt found. Let's create one!")
        print("-" * 70)
        description = input("\nWhat do you want to build? (brief description): ").strip()

        if not description:
            print("Error: Please provide a description of what you want to build.")
            return

        spec_created = run_interactive_spec_generation(project_dir, description, model)
        if not spec_created:
            print("\nExiting. Run again to retry spec generation.")
            return

        print("\nContinuing to autonomous coding...\n")

    # Step 2: Check if this is a fresh start or continuation
    tests_file = project_dir / "feature_list.json"
    is_first_run = not tests_file.exists()

    if is_first_run:
        print("Fresh start - will use initializer agent")
        print()
        print("=" * 70)
        print("  NOTE: First session takes 10-20+ minutes!")
        print("  The agent is generating 200 detailed test cases.")
        print("  This may appear to hang - it's working.")
        print("=" * 70)
        print()
    else:
        print("Continuing existing project")
        print_progress_summary(project_dir)

    # Main loop
    iteration = 0

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Print session header
        print_session_header(iteration, is_first_run)

        # Choose prompt based on session type
        if is_first_run:
            prompt = get_initializer_prompt()
            is_first_run = False  # Only use initializer once
        else:
            prompt = get_coding_prompt()

        # Run session
        output, return_code = run_cli_session(project_dir, prompt, model)

        print("\n" + "-" * 70)

        if return_code == 0:
            print(f"\nSession completed. Auto-continuing in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
            time.sleep(AUTO_CONTINUE_DELAY_SECONDS)
        else:
            print(f"\nSession ended with code {return_code}")
            if output:
                print(f"Error: {output}")
            print("Will retry with a fresh session...")
            time.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            time.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

    # Print instructions for running the generated application
    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Run the setup script")
    print("  # Or manually:")
    print("  npm install && npm run dev")
    print("\n  Then open http://localhost:3000 (or check init.sh for the URL)")
    print("-" * 70)

    print("\nDone!")
