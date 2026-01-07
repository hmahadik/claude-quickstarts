"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

import shutil
from pathlib import Path


# Prompts are in the parent directory's prompts folder
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    return prompt_path.read_text()


def get_initializer_prompt(feature_count: int = 10) -> str:
    """Load the initializer prompt with configurable feature count."""
    template = load_prompt("initializer_prompt")
    return template.replace("{feature_count}", str(feature_count))


def get_coding_prompt() -> str:
    """Load the coding agent prompt."""
    return load_prompt("coding_prompt")


def get_enhancer_prompt() -> str:
    """Load the enhancer prompt for existing projects."""
    return load_prompt("enhancer_prompt")


def get_spec_generator_prompt(description: str) -> str:
    """Load the spec generator prompt with the user's description."""
    template = load_prompt("spec_generator_prompt")
    return template.replace("{description}", description)


def get_app_audit_prompt() -> str:
    """Load the app audit prompt for generating specs from existing codebases."""
    return load_prompt("app_audit_prompt")


def get_qa_prompt() -> str:
    """Load the visual QA agent prompt."""
    return load_prompt("qa_prompt")


def copy_spec_to_project(project_dir: Path) -> None:
    """Copy the app spec file into the project directory for the agent to read."""
    spec_source = PROMPTS_DIR / "app_spec.txt"
    spec_dest = project_dir / "app_spec.txt"
    if not spec_dest.exists():
        shutil.copy(spec_source, spec_dest)
        print("Copied app_spec.txt to project directory")
