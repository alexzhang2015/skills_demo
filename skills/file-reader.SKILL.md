---
name: file-reader
description: Read and display file contents. Use when user wants to view, read, or show a file.
allowed_tools:
  - read
  - glob
model: claude-sonnet-4-20250514
---

# File Reader Skill

Read files from the filesystem and display their contents.

## Instructions

1. If the user provides a specific file path, read that file directly
2. If the user provides a pattern or filename without path, use glob to find matching files
3. Display the file contents with proper formatting
4. For large files, show a summary or the first portion

## Examples

User: "read the config file"
Action: Use glob to find config files (*.json, *.yaml, *.toml, config.*), then read the most relevant one

User: "show me app.py"
Action: Search for app.py in the project and read its contents

User: "what's in the README"
Action: Read README.md or README files in the current directory
