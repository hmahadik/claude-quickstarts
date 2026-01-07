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
from typing import Literal, Optional

from progress import print_session_header, print_progress_summary
from prompts import (
    get_initializer_prompt,
    get_coding_prompt,
    get_spec_generator_prompt,
    get_enhancer_prompt,
    get_app_audit_prompt,
    get_qa_prompt,
)


# Type alias for project maturity
ProjectMaturity = Literal["greenfield", "existing"]


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


def detect_project_maturity(project_dir: Path) -> tuple[ProjectMaturity, dict]:
    """
    Detect whether a project is greenfield or an existing codebase.

    Uses git history and source file presence to determine maturity.
    A project is considered "existing" if it has:
    - A git repository with 5+ commits
    - At least one source file

    Args:
        project_dir: Directory to analyze

    Returns:
        Tuple of (maturity_type, details_dict)
        - maturity_type: "greenfield" | "existing"
        - details_dict: Contains detection information
    """
    details = {
        "has_git": False,
        "commit_count": 0,
        "source_files_found": [],
        "detected_languages": [],
    }

    # Check for .git directory
    git_dir = project_dir / ".git"
    details["has_git"] = git_dir.exists()

    # Count commits if git exists
    if details["has_git"]:
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                details["commit_count"] = int(result.stdout.strip())
        except (subprocess.TimeoutExpired, ValueError):
            pass

    # Check for source files
    source_extensions = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript/React",
        ".jsx": "JavaScript/React",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".php": "PHP",
    }

    for ext, lang in source_extensions.items():
        # Use glob to find files (limit to prevent slowdown on large repos)
        files = list(project_dir.rglob(f"*{ext}"))[:5]
        if files:
            details["source_files_found"].extend(
                [str(f.relative_to(project_dir)) for f in files[:3]]
            )
            if lang not in details["detected_languages"]:
                details["detected_languages"].append(lang)

    # Maturity determination:
    # - "existing" if: has_git AND commit_count >= 5 AND has source files
    # - "greenfield" otherwise
    is_existing = (
        details["has_git"]
        and details["commit_count"] >= 5
        and len(details["source_files_found"]) > 0
    )

    maturity: ProjectMaturity = "existing" if is_existing else "greenfield"
    return maturity, details


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


def run_interactive_audit(
    project_dir: Path,
    model: str,
) -> bool:
    """
    Run an interactive Claude session to audit an existing codebase and generate a spec.

    The user will have a conversation with Claude about what the app should do,
    what's broken, and what needs improvement. Claude will write app_spec.txt
    as a prescriptive roadmap.

    Args:
        project_dir: Directory containing the existing project
        model: Model to use

    Returns:
        True if app_spec.txt was created, False otherwise
    """
    print("\n" + "=" * 70)
    print("  APP AUDIT (Interactive)")
    print("=" * 70)
    print("\nClaude will analyze your codebase and interview you about:")
    print("  - What the app should do (the vision)")
    print("  - What's currently working vs broken")
    print("  - What needs to be fixed, completed, or added")
    print("\nThe resulting spec will be a ROADMAP, not just documentation.")
    print("Once the spec is generated, exit the session (Ctrl+C or /exit).")
    print("-" * 70)
    print("\n>>> Type 'start' or press Enter to begin the audit <<<\n")

    system_prompt = get_app_audit_prompt()

    cmd = [
        "claude",
        "--system-prompt", system_prompt,
        "--model", model,
    ]

    try:
        # Run interactively (no -p flag, no capture)
        subprocess.run(cmd, cwd=project_dir)
    except KeyboardInterrupt:
        print("\n\nAudit session ended.")
    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Ensure Claude Code is installed.")
        return False

    # Check if spec was created
    spec_file = project_dir / "app_spec.txt"
    if spec_file.exists():
        print("\n" + "=" * 70)
        print("  app_spec.txt created successfully!")
        print("  This spec describes what your app SHOULD do.")
        print("  The coding agent will use it to fix, complete, and enhance.")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("  Warning: app_spec.txt was not created.")
        print("  Run again with --audit to retry.")
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
        "--dangerously-skip-permissions",
        "--chrome",
    ]

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_dir}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=False,  # Let output stream to terminal
            text=True
        )
        return "", result.returncode
    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Ensure Claude Code is installed.")
        return "claude CLI not found", 1
    except Exception as e:
        return str(e), 1


def run_qa_session(
    project_dir: Path,
    model: str,
) -> tuple[str, int]:
    """
    Run a visual QA session after the coding agent completes.

    The QA agent reviews the application visually, looking for UI/UX issues,
    and documents any problems found for the next coding session to address.

    Args:
        project_dir: Directory to run in (cwd)
        model: Model to use

    Returns:
        (output, return_code) tuple
    """
    print("\n" + "=" * 70)
    print("  VISUAL QA AGENT")
    print("=" * 70)
    print("\nRunning hypercritical visual QA review...")
    print("The QA agent will inspect the app and document any issues found.")
    print("-" * 70 + "\n")

    prompt = get_qa_prompt()

    cmd = [
        "claude",
        "-p", prompt,
        "--model", model,
        "--dangerously-skip-permissions",
        "--chrome",
    ]

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_dir}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=False,  # Let output stream to terminal
            text=True
        )
        return "", result.returncode
    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Ensure Claude Code is installed.")
        return "claude CLI not found", 1
    except Exception as e:
        return str(e), 1


def run_non_interactive_spec_generation(
    project_dir: Path,
    description: str,
    model: str,
) -> bool:
    """
    Generate app specification non-interactively using a single prompt.

    Captures Claude's output and writes the spec file directly to avoid
    permission prompts in non-interactive mode.

    Args:
        project_dir: Directory for the project
        description: User's description of what to build
        model: Model to use

    Returns:
        True if app_spec.txt was created, False otherwise
    """
    print("\n" + "=" * 70)
    print("  SPEC GENERATION (Non-Interactive)")
    print("=" * 70)
    print(f"\nGenerating spec from description: {description}")
    print("-" * 70 + "\n")

    system_prompt = get_spec_generator_prompt(description)

    # Ask Claude to output the spec content directly (we'll write the file)
    prompt = f"""Based on the description provided in the system prompt, generate a complete app specification.

Do NOT ask any clarifying questions - make reasonable assumptions and create a comprehensive specification.

Output ONLY the specification content with no additional commentary or markdown formatting.
Do NOT use any tools - just output the raw specification text."""

    cmd = [
        "claude",
        "--system-prompt", system_prompt,
        "--model", model,
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--output-format=stream-json",
        "--verbose",
    ]

    try:
        result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Spec generation failed with code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False

        # Write the spec content to file
        spec_content = result.stdout.strip()
        if not spec_content:
            print("Error: No spec content generated")
            return False

        spec_file = project_dir / "app_spec.txt"
        spec_file.write_text(spec_content)
        print(f"Wrote {len(spec_content)} characters to app_spec.txt")

    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Ensure Claude Code is installed.")
        return False

    # Verify the file was created
    spec_file = project_dir / "app_spec.txt"
    if spec_file.exists():
        print("\n" + "=" * 70)
        print("  app_spec.txt created successfully!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("  Warning: app_spec.txt was not created.")
        print("=" * 70)
        return False


def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: Optional[int] = None,
    description: Optional[str] = None,
    non_interactive: bool = False,
    audit: bool = False,
    feature_count: int = 10,
) -> None:
    """
    Run the autonomous agent loop using Claude CLI.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
        description: Project description for spec generation (optional)
        non_interactive: If True, skip interactive prompts
        audit: If True, run audit mode to generate spec from existing codebase
        feature_count: Number of features to generate in feature_list.json
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

    # Detect project maturity (needed for routing decisions)
    maturity, maturity_details = detect_project_maturity(project_dir)

    # Step 1: Check if app_spec.txt exists - if not, run spec generation
    spec_file = project_dir / "app_spec.txt"

    if not spec_file.exists():
        print("\n" + "-" * 70)
        print("No app_spec.txt found. Let's create one!")
        print("-" * 70)

        # If --audit flag was passed, or this is an existing project, consider audit mode
        if audit:
            # Explicit audit mode requested
            spec_created = run_interactive_audit(project_dir, model)
            if not spec_created:
                print("\nExiting. Run again with --audit to retry.")
                return
        elif maturity == "existing" and not non_interactive:
            # Existing project detected - offer audit mode
            print(f"\n  Detected existing project:")
            print(f"    - Git commits: {maturity_details['commit_count']}")
            if maturity_details['detected_languages']:
                print(f"    - Languages: {', '.join(maturity_details['detected_languages'])}")
            print()
            print("  Options:")
            print("    1. AUDIT mode - Generate spec from existing code (recommended)")
            print("       Claude will analyze your code and interview you about")
            print("       what's working, broken, and needs improvement.")
            print()
            print("    2. NEW SPEC mode - Describe what you want from scratch")
            print("       Ignores existing code, creates spec from your description.")
            print()

            try:
                choice = input("Choose [1/2] (default: 1): ").strip()
            except EOFError:
                choice = "1"

            if choice != "2":
                # Run audit mode
                spec_created = run_interactive_audit(project_dir, model)
                if not spec_created:
                    print("\nExiting. Run again with --audit to retry.")
                    return
            else:
                # Fall through to standard spec generation
                if description is None:
                    try:
                        description = input("\nWhat do you want to build? (brief description): ").strip()
                    except EOFError:
                        print("\nError: No description provided.")
                        return

                if not description:
                    print("Error: Please provide a description of what you want to build.")
                    return

                spec_created = run_interactive_spec_generation(project_dir, description, model)
                if not spec_created:
                    print("\nExiting. Run again to retry spec generation.")
                    return
        else:
            # Greenfield project or non-interactive mode - standard spec generation
            if description is None:
                try:
                    description = input("\nWhat do you want to build? (brief description): ").strip()
                except EOFError:
                    print("\nError: No description provided and running non-interactively.")
                    print("Use --description 'your description' to provide a description.")
                    return

            if not description:
                print("Error: Please provide a description of what you want to build.")
                return

            if non_interactive:
                spec_created = run_non_interactive_spec_generation(project_dir, description, model)
            else:
                spec_created = run_interactive_spec_generation(project_dir, description, model)
            if not spec_created:
                print("\nExiting. Run again to retry spec generation.")
                return

        print("\nContinuing to autonomous coding...\n")

    # Step 2: Determine session type and select first-run prompt
    tests_file = project_dir / "feature_list.json"
    is_first_run = not tests_file.exists()
    first_prompt = None  # Will hold initializer or enhancer prompt if needed

    if is_first_run:
        # Use maturity detected earlier to choose appropriate first-run prompt
        if maturity == "existing":
            # Existing project - use enhancer mode
            first_prompt = get_enhancer_prompt()
            print("=" * 70)
            print("  ENHANCEMENT MODE")
            print("=" * 70)
            print(f"\n  Detected existing project:")
            print(f"    - Git commits: {maturity_details['commit_count']}")
            if maturity_details['detected_languages']:
                print(f"    - Languages: {', '.join(maturity_details['detected_languages'])}")
            if maturity_details['source_files_found']:
                sample_files = maturity_details['source_files_found'][:3]
                print(f"    - Sample files: {', '.join(sample_files)}")
            print("\n  Will create tests for NEW features only (from app_spec.txt)")
            print("  Existing functionality will not be re-tested.")
            print("=" * 70)
            print()
        else:
            # Greenfield project - use initializer
            first_prompt = get_initializer_prompt(feature_count=feature_count)
            print("Fresh start - will use initializer agent")
            print(f"  Feature count: {feature_count}")
            print()
            print("=" * 70)
            print("  NOTE: First session takes 10-20+ minutes!")
            print("  The agent is generating detailed test cases.")
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
        if first_prompt is not None:
            prompt = first_prompt
            first_prompt = None  # Only use initializer/enhancer once
        else:
            prompt = get_coding_prompt()

        # Run session
        output, return_code = run_cli_session(project_dir, prompt, model)

        print("\n" + "-" * 70)

        if return_code == 0:
            print(f"\nCoding session completed successfully.")
            print_progress_summary(project_dir)

            # Run QA agent after successful coding sessions (skip first run which is just setup)
            if not is_first_run or iteration > 1:
                print(f"\nStarting QA review in {AUTO_CONTINUE_DELAY_SECONDS}s...")
                time.sleep(AUTO_CONTINUE_DELAY_SECONDS)

                qa_output, qa_return_code = run_qa_session(project_dir, model)

                if qa_return_code == 0:
                    print("\nQA review completed.")
                else:
                    print(f"\nQA session ended with code {qa_return_code}")
                    if qa_output:
                        print(f"Error: {qa_output}")

                print_progress_summary(project_dir)
            else:
                print("\nSkipping QA for initialization session.")

            print(f"\nAuto-continuing in {AUTO_CONTINUE_DELAY_SECONDS}s...")
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
