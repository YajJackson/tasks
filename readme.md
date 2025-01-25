# Tasks (name tbd)


## Overview
Minimal task management directly in your shell.


## Features
- **Add Tasks**: Create tasks with a description and a unique ID.
- **List Tasks**: View all tasks interactively, toggle their status (TODO ↔ DONE).
- **Show Task Details**: Display detailed information about a specific task.
- **Persistent Storage**: Tasks are saved in a JSON file for persistence.


## Demo
![Task Program Demo](./docs/task_demo.gif)


## Prerequisites
- [`jq`](https://stedolan.github.io/jq/) (for JSON manipulation)
- [`gum`](https://github.com/charmbracelet/gum) (for interactive UI)


## Installation
1. Ensure `jq` and `gum` are installed:
   ```bash
   sudo apt install jq       # Debian/Ubuntu
   brew install jq gum       # macOS
   ```
2. Save the script to a file, e.g., `task`.
3. Make the script executable:
   ```bash
   chmod +x task
   ```
4. Move it to your PATH for easy access:
   ```bash
   mv task /usr/local/bin/task
   ```


## Usage

### Add a Task
```bash
task add "Finish project report"
```


### Show Task Details
```bash
task show <task_id>
```
If `<task_id>` is omitted, an interactive menu will appear, allowing you to select a task.


### List and Manage Tasks
```bash
task list
```
- Press **Space** to toggle a task's status (📝 ↔ ✅).
- Press **Enter** to confirm your selection.


## File Structure
- Tasks are stored persistently in `.project_tasks/tasks.json` in your current directory.
- Example task format:
  ```json
  [
    {
      "id": "1672527600",
      "description": "Complete project documentation",
      "date": "2025-01-24 12:00:00",
      "status": "TODO"
    }
  ]
  ```


## Notes
- Tasks are sorted by their status (`📝 TODO` first, then `✅ DONE`) and by creation date.

