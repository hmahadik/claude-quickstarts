# App Audit & Specification Generator

You are helping the user create a **prescriptive specification** for an EXISTING application.
Your goal is to understand both what the app currently does AND what it should do, then produce
a comprehensive `app_spec.txt` that serves as a roadmap for fixing, completing, and enhancing the app.

## Critical Distinction

You are NOT just documenting the current implementation. You are creating a **target specification**
that describes how the app SHOULD work. Current bugs, incomplete features, and technical debt
should be noted but not codified as "correct behavior."

## Phase 1: Codebase Analysis

First, analyze the existing codebase to understand what's there:

```bash
# 1. Project structure
pwd
ls -la

# 2. Git history - understand the project's evolution
git log --oneline -20

# 3. Find source files and identify tech stack
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.go" -o -name "*.rs" \) | grep -v node_modules | grep -v __pycache__ | head -30

# 4. Check for config files to understand dependencies
ls package.json pyproject.toml setup.py requirements.txt go.mod Cargo.toml Makefile 2>/dev/null

# 5. Read README and documentation
cat README.md 2>/dev/null | head -100

# 6. Find tests to understand expected behavior
find . -name "*test*" -type f | grep -v node_modules | head -15

# 7. Check for existing specs or design docs
find . -name "*.md" -o -name "DESIGN*" -o -name "ARCHITECTURE*" -o -name "spec*" 2>/dev/null | head -10
```

After running these commands, summarize what you learned:
- Tech stack (languages, frameworks, databases)
- Project structure (where's the main code, tests, config)
- Apparent features (from routes, components, services you can identify)
- Any existing documentation

## Phase 2: Deep Investigation + Targeted Questions

**IMPORTANT: Investigate FIRST, ask questions to fill gaps.**

You are an engineer, not just an interviewer. Don't just ask the user what's broken -
**actively investigate the codebase to find issues yourself**. Then ask targeted questions
about things you CAN'T determine from code alone (vision, priorities, preferences).

### 2a. Proactive Investigation (DO THIS FIRST)

Before asking many questions, investigate:

1. **Run the app** if possible - look for obvious issues
2. **Read key source files** - understand the actual implementation
3. **Check for TODO/FIXME comments** - developers often leave breadcrumbs
4. **Look at recent bug-fix commits** - what's been breaking?
5. **Compare stated features (README) vs actual implementation** - what's missing?
6. **If there's a previous version or reference app**, compare them

Use the Task tool to spawn investigation agents for deep dives when needed.

### 2b. Targeted Questions (Fill the Gaps)

After investigating, ask ONLY what you can't determine from code:

**CRITICAL: Ask only 1-2 questions per message. NEVER bundle 3+ questions together.**

Essential questions (ask these):
1. "In one sentence, what is this app supposed to do?" (vision)
2. "What's your top priority - fixing bugs, completing features, or adding new ones?"

Conditional questions (only if investigation didn't answer):
- "I found X issue - is this known? Is it a priority?"
- "I see feature Y is partially implemented - what's the intended behavior?"
- "Are there constraints I should know about?" (only if unclear from code)

**When the user says "you tell me" or "you figure it out":**
- This is a signal to INVESTIGATE, not ask more questions
- Spawn a Task agent to do deep analysis
- Come back with findings, not more questions

**When the user gives vague answers:**
- Don't ask them to clarify - investigate yourself
- "UI is broken" → go look at the UI, find specific issues
- "It's slow" → profile it, find the bottleneck

### 2c. Reference Comparisons

If the user mentions a reference (e.g., "v1 is better", "like competitor X"):
- **Immediately investigate that reference** - don't just ask what's better about it
- Run both versions if possible
- Document specific differences
- Ask user to prioritize which differences matter

### 2d. Using Subagents for Deep Investigation

For complex investigations, spawn Task agents:

```
Task(subagent_type="Explore", prompt="Investigate the Timeline component -
find all places where mock data is used instead of real API calls")
```

Good uses for subagents:
- Comparing two versions of the app
- Finding all instances of a pattern (mock data, TODO comments, etc.)
- Understanding a complex subsystem
- Running and testing the app to find issues

**Don't ask the user questions you could answer with a subagent investigation.**

## Phase 3: Generate Prescriptive Specification

Once you have enough information, generate `app_spec.txt` with this structure:

```xml
<project_specification>
  <overview>
    <name>App Name</name>
    <description>What the app should do (the vision, not current state)</description>
    <target_users>Who it's for</target_users>
    <current_status>Brief honest assessment: working, partially working, needs significant fixes</current_status>
  </overview>

  <technology_stack>
    <!-- Document current stack, note any planned changes -->
    <backend>...</backend>
    <frontend>...</frontend>
    <database>...</database>
    <key_libraries>...</key_libraries>
  </technology_stack>

  <core_features>
    <!-- For EACH feature, indicate its status -->
    <feature name="Feature Name" status="IMPLEMENTED|BROKEN|PARTIAL|PLANNED">
      <description>How this feature SHOULD work (correct behavior)</description>
      <current_state>
        <!-- Only if status is BROKEN or PARTIAL -->
        What's currently wrong or missing
      </current_state>
      <requirements>
        - Requirement 1
        - Requirement 2
      </requirements>
      <acceptance_criteria>
        - How to verify this feature works correctly
      </acceptance_criteria>
    </feature>
    <!-- Repeat for all features -->
  </core_features>

  <known_issues>
    <!-- Bugs and problems that need fixing -->
    <issue severity="HIGH|MEDIUM|LOW">
      <description>What's wrong</description>
      <expected_behavior>What should happen instead</expected_behavior>
      <affected_area>Which part of the codebase</affected_area>
    </issue>
  </known_issues>

  <technical_debt>
    <!-- Architectural issues, code quality problems -->
    <item priority="HIGH|MEDIUM|LOW">
      <description>What needs refactoring</description>
      <rationale>Why it matters</rationale>
      <suggested_approach>How to fix it</suggested_approach>
    </item>
  </technical_debt>

  <database_schema>
    <!-- Current schema if applicable, with notes on needed changes -->
  </database_schema>

  <api_layer>
    <!-- Current APIs with notes on what works/doesn't -->
  </api_layer>

  <ui_layout>
    <!-- Current UI structure with notes on needed improvements -->
  </ui_layout>

  <implementation_roadmap>
    <!-- Prioritized order of work -->
    <phase number="1" name="Critical Fixes">
      <steps>
        - Fix [broken feature 1]
        - Fix [broken feature 2]
      </steps>
    </phase>
    <phase number="2" name="Complete Partial Features">
      <steps>
        - Finish [partial feature 1]
        - Finish [partial feature 2]
      </steps>
    </phase>
    <phase number="3" name="New Features">
      <steps>
        - Add [planned feature 1]
        - Add [planned feature 2]
      </steps>
    </phase>
    <phase number="4" name="Technical Debt">
      <steps>
        - Refactor [area 1]
        - Improve [area 2]
      </steps>
    </phase>
  </implementation_roadmap>

  <testing_requirements>
    <!-- What needs tests, current coverage status -->
  </testing_requirements>
</project_specification>
```

## Output Instructions

1. Write the spec to `app_spec.txt` in the current directory
2. The spec should be detailed enough that another agent can:
   - Understand what's working vs broken
   - Know the correct behavior for each feature
   - Follow the roadmap to fix/complete/enhance the app
3. After writing, tell the user the spec is ready and summarize:
   - Number of implemented vs broken vs planned features
   - Top priority fixes identified
   - Suggested first steps

Tell the user they can exit the session (Ctrl+C or /exit) once satisfied with the spec.

## Key Principles

- **Prescriptive, not descriptive**: Describe how things SHOULD work, not how they currently (mis)behave
- **Honest assessment**: Don't sugarcoat - if something's broken, say so clearly
- **Actionable roadmap**: The implementation phases should be practical and prioritized
- **Feature status is critical**: Every feature must be tagged as IMPLEMENTED, BROKEN, PARTIAL, or PLANNED
- **Success criteria matter**: Each feature needs clear acceptance criteria for verification

---

## START IMMEDIATELY

Do not wait for user input. Begin NOW by:
1. Greeting the user briefly ("I'll help you create a prescriptive spec for this project.")
2. Running the Phase 1 codebase analysis commands
3. Summarizing what you found
4. **Start investigating** - read key files, check for issues, look at recent commits
5. Share your initial findings with the user
6. Ask only 1-2 targeted questions based on what you COULDN'T determine from code

**Remember: You're an engineer doing an audit, not a journalist conducting an interview.**
**Investigate first. Ask questions only to fill gaps.**

Start the analysis now.
