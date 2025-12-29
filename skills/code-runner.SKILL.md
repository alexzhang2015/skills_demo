---
name: code-runner
description: Execute code and shell commands. Use when user wants to run, execute, or test code.
allowed_tools:
  - bash
  - read
model: claude-sonnet-4-20250514
---

# Code Runner Skill

Execute code snippets and shell commands safely.

## Instructions

1. Analyze what the user wants to run
2. For Python: use `python -c "code"` or `python script.py`
3. For Node.js: use `node -e "code"` or `node script.js`
4. For shell commands: execute directly with bash
5. Always show the output and any errors

## Safety Rules

- Do not run destructive commands (rm -rf, format, etc.)
- Do not access sensitive files (/etc/passwd, ~/.ssh, etc.)
- Timeout long-running commands after 30 seconds

## Examples

User: "run the tests"
Action: Execute `pytest` or `npm test` based on project type

User: "check python version"
Action: Run `python --version`

User: "list all files"
Action: Run `ls -la` or appropriate listing command
