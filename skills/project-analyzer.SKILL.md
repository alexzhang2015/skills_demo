---
name: project-analyzer
description: Analyze project structure and provide overview. Use when user wants to understand or explore a codebase.
allowed_tools:
  - bash
  - read
  - glob
  - grep
model: claude-sonnet-4-20250514
---

# Project Analyzer Skill

Analyze and summarize project structure and codebase.

## Instructions

1. Use glob to find key project files
2. Read configuration files (package.json, pyproject.toml, etc.)
3. List directory structure
4. Identify project type and technologies used

## Analysis Steps

1. **Identify project type**: Check for package.json (Node), pyproject.toml (Python), Cargo.toml (Rust), etc.
2. **Find entry points**: Look for main.py, index.js, app.py, etc.
3. **List dependencies**: Read package manager files
4. **Show structure**: Use `tree` or `ls -R` for directory overview

## Examples

User: "analyze this project"
Action: Find and read config files, show directory structure

User: "what technologies are used"
Action: Read package files to identify dependencies and frameworks

User: "show project structure"
Action: Display directory tree or file listing
