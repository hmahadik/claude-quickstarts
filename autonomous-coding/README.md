# Autonomous Coding Agent Demo

A minimal harness demonstrating long-running autonomous coding with Claude. This demo implements a two-agent pattern (initializer + coding agent) that can build complete applications over multiple sessions.

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

For testing with limited iterations:
```bash
python run_autonomous.py --project-dir ./my_project --max-iterations 3
```

## How It Works

### Three-Phase Flow

1. **Spec Generation (Interactive):** If no `app_spec.txt` exists, Claude interviews you to understand requirements and generates a detailed specification.

2. **Initializer Agent (Session 1):** Reads `app_spec.txt`, creates `feature_list.json` with 200 test cases, sets up project structure, and initializes git.

3. **Coding Agent (Sessions 2+):** Picks up where the previous session left off, implements features one by one, and marks them as passing in `feature_list.json`.

### Session Management

- Each session runs with a fresh context window
- Progress persists via `feature_list.json` and git commits
- Auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run the same command to resume

## Important Timing Expectations

> **Warning: This demo takes a long time to run!**

- **First session (initialization):** Generates `feature_list.json` with 200 test cases. Takes 10-20+ minutes and may appear to hang - this is normal.
- **Subsequent sessions:** Each coding iteration can take 5-15 minutes.
- **Full app:** Building all 200 features typically requires many hours across multiple sessions.

**Tip:** Modify `prompts/initializer_prompt.md` to reduce the feature count (e.g., 20-50) for faster demos.

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
│   ├── initializer_prompt.md     # First session prompt
│   └── coding_prompt.md          # Continuation session prompt
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

## Customization

### Providing Your Own Spec

To skip the interactive spec generation, create `app_spec.txt` in your project directory before running. The agent will use your existing spec instead of interviewing you.

### Adjusting Feature Count

Edit `prompts/initializer_prompt.md` and change the "200 features" requirement.

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
This is normal. The initializer agent is generating 200 detailed test cases. Watch for output to confirm the agent is working.

**"Command blocked by security hook"**
The agent tried to run a command not in the allowlist. Add the command to `ALLOWED_COMMANDS` in the security hook if needed.

**"claude CLI not found"**
Ensure Claude Code is installed: `npm install -g @anthropic-ai/claude-code`

**"API key not set"**
Ensure `ANTHROPIC_API_KEY` is exported in your shell environment.

## License

Internal Anthropic use.
