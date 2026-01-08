# Autonomous Coding Agent Demo

A minimal harness demonstrating long-running autonomous coding with Claude. This demo implements a multi-agent pattern (initializer + coding agent + QA agent) that can build complete applications over multiple sessions.

Two implementations are available:
- **CLI Harness** (recommended): Uses Claude Code CLI via subprocess - simpler setup, fewer dependencies
- **SDK Version**: Uses Claude Agent SDK directly - more control, programmatic access

## Prerequisites

**Claude Code CLI** (required for CLI harness):
```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

**API Key:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Quick Start (CLI Harness)

```bash
cd cli
python run_autonomous.py --project-dir ./my_project
```

On first run, you'll be prompted:
```
What do you want to build? (brief description): A task management app with projects and due dates
```

Claude will then interview you to understand your requirements, generate `app_spec.txt`, and begin autonomous coding.

### Common Usage Patterns

```bash
# Start a new project (interactive spec generation)
python run_autonomous.py --project-dir ./my-app

# Start with a description (skips initial prompt)
python run_autonomous.py --project-dir ./my-app --description "Build a claude.ai clone"

# Fully non-interactive (auto-generates spec without interview)
python run_autonomous.py --project-dir ./my-app --description "A todo app" --non-interactive

# Audit an existing codebase to generate a prescriptive spec
python run_autonomous.py --project-dir ./existing-app --audit

# Generate more features (default: 10)
python run_autonomous.py --project-dir ./my-app --feature-count 25

# Limit iterations for testing
python run_autonomous.py --project-dir ./my_project --max-iterations 3
```

## How It Works

### Multi-Phase Flow

1. **Spec Generation:** If no `app_spec.txt` exists:
   - **Interactive mode (default):** Claude interviews you to understand requirements
   - **Non-interactive mode:** Claude generates a spec from your `--description`
   - **Audit mode:** Claude analyzes existing code and interviews you about what's working, broken, and needs improvement

2. **Project Detection:** The harness auto-detects whether you have a greenfield or existing project:
   - **Greenfield:** Uses the **Initializer Agent** to set up project structure and create `feature_list.json`
   - **Existing (5+ git commits):** Uses the **Enhancer Agent** to create tests for NEW features only

3. **Coding Agent (Sessions 2+):** Picks up where the previous session left off, implements features one by one, and marks them as passing in `feature_list.json`.

4. **Visual QA Agent:** After each coding session completes, a QA agent reviews the application visually using browser automation, looking for UI/UX issues and documenting problems for the next session.

### Session Management

- Each session runs with a fresh context window
- Progress persists via `feature_list.json` and git commits
- Visual QA runs after each successful coding session
- Auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run the same command to resume

## Important Timing Expectations

> **Note: This demo takes a long time to run!**

- **First session (initialization):** Generates `feature_list.json` with test cases (default: 10 features). Takes 10-20+ minutes and may appear to hang - this is normal.
- **Subsequent sessions:** Each coding iteration can take 5-15 minutes, followed by visual QA review.
- **Full app:** Building all features requires multiple sessions. Use `--feature-count` to control scope.

**Tip:** Use `--feature-count 5` for quick demos, or `--feature-count 50` for more comprehensive applications.

## Security Model

The CLI harness uses Claude Code hooks for security:

1. **Bash Command Allowlist:** Only specific commands are permitted via a PreToolUse hook
2. **Filesystem Restrictions:** File operations restricted to the project directory via Claude Code's built-in sandboxing

Allowed commands:
- File inspection: `ls`, `cat`, `head`, `tail`, `wc`, `grep`
- File operations: `cp`, `mkdir`, `chmod` (+x only)
- Node.js: `npm`, `node`
- Version control: `git`
- Process management: `ps`, `lsof`, `sleep`, `pkill` (dev processes only)

The security hook (`cli/.claude/hooks/validate-bash.py`) is automatically copied to the project directory on startup.

## Project Structure

```
autonomous-coding/
├── cli/                          # CLI harness (recommended)
│   ├── run_autonomous.py         # Entry point
│   ├── orchestrator.py           # Session management
│   ├── prompts.py                # Prompt loading
│   ├── progress.py               # Progress utilities
│   └── .claude/
│       ├── settings.json         # Claude Code settings
│       └── hooks/
│           └── validate-bash.py  # Security hook
├── prompts/
│   ├── app_spec.txt              # Example application specification
│   ├── spec_generator_prompt.md  # Spec generation interview prompt
│   ├── app_audit_prompt.md       # Existing codebase audit prompt
│   ├── initializer_prompt.md     # First session prompt (greenfield)
│   ├── enhancer_prompt.md        # First session prompt (existing projects)
│   ├── coding_prompt.md          # Continuation session prompt
│   └── qa_prompt.md              # Visual QA agent prompt
├── autonomous_agent_demo.py      # SDK version entry point
├── agent.py                      # SDK version agent logic
├── client.py                     # SDK version client config
├── security.py                   # SDK version security
└── requirements.txt              # Python dependencies (SDK version)
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── feature_list.json         # Test cases (source of truth)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── .claude/                  # Claude Code settings and hooks
└── [application files]       # Generated application code
```

## Running the Generated Application

```bash
cd my_project
./init.sh           # Run the setup script

# Or manually:
npm install
npm run dev
```

The application will typically be available at `http://localhost:3000`.

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | Required |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-sonnet-4-5-20250929` |
| `--description` | Project description (skips initial prompt) | None |
| `--non-interactive` | Generate spec without interview | `false` |
| `--audit` | Audit existing codebase for spec generation | `false` |
| `--feature-count` | Number of features to generate | `10` |

## Customization

### Providing Your Own Spec

To skip the interactive spec generation, create `app_spec.txt` in your project directory before running. The agent will use your existing spec instead of interviewing you.

### Adjusting Feature Count

Use the `--feature-count` option to control how many features are generated:
```bash
python run_autonomous.py --project-dir ./my-app --feature-count 25
```

### Audit Mode for Existing Projects

When working with an existing codebase, use `--audit` to have Claude analyze the code and generate a prescriptive spec (what the app SHOULD do, not just what it currently does):
```bash
python run_autonomous.py --project-dir ./existing-app --audit
```

The audit mode:
- Analyzes your existing code structure
- Interviews you about what's working vs. broken
- Generates a spec as a roadmap for improvements
- The enhancer agent then creates tests only for NEW features

### Modifying Allowed Commands

Edit `cli/.claude/hooks/validate-bash.py` to add or remove commands from `ALLOWED_COMMANDS`.

## SDK Version (Alternative)

For more programmatic control, use the SDK-based implementation:

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python autonomous_agent_demo.py --project-dir ./my_project
```

The SDK version uses `client.py` for Claude SDK configuration and `security.py` for bash validation.

## Troubleshooting

**"Appears to hang on first run"**
This is normal. The initializer agent is generating detailed test cases. Watch for output to confirm the agent is working.

**"Command blocked by security hook"**
The agent tried to run a command not in the allowlist. Add the command to `ALLOWED_COMMANDS` in the security hook if needed.

**"claude CLI not found"**
Ensure Claude Code is installed: `npm install -g @anthropic-ai/claude-code`

**"API key not set"**
Ensure `ANTHROPIC_API_KEY` is exported in your shell environment.

**"QA agent failing"**
The visual QA agent requires browser automation (Chrome). Ensure you have the Claude-in-Chrome extension set up for browser access.

## License

Internal Anthropic use.
