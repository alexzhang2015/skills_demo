---
name: git-helper
description: Git operations including status, diff, log, and branch management. Use for version control tasks.
allowed_tools:
  - bash
  - read
model: claude-sonnet-4-20250514
---

# Git Helper Skill

Perform Git version control operations.

## Instructions

1. Understand what Git operation the user needs
2. Execute the appropriate git command
3. Format and explain the output clearly

## Supported Operations

- **Status**: `git status` - show working tree status
- **Diff**: `git diff` - show changes
- **Log**: `git log --oneline -10` - recent commits
- **Branch**: `git branch` - list branches
- **Current branch**: `git branch --show-current`

## Safety Rules

- Do NOT run `git push --force`
- Do NOT run `git reset --hard` without confirmation
- Do NOT modify git config

## Examples

User: "show git status"
Action: Run `git status`

User: "what changed"
Action: Run `git diff` to show uncommitted changes

User: "show recent commits"
Action: Run `git log --oneline -10`
