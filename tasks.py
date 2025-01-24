import argparse
import json
import os
import uuid
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich.align import Align
from rich.panel import Panel

TASKS_DIR = ".project_tasks"
TASKS_FILE = os.path.join(TASKS_DIR, "tasks.json")
console = Console()


# Ensure the tasks directory and file exist
def ensure_tasks_file():
    if not os.path.exists(TASKS_DIR):
        os.makedirs(TASKS_DIR)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w") as f:
            json.dump([], f)


# Load tasks from file
def load_tasks():
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


# Save tasks to file
def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


# Add a new task
def add_task(description):
    ensure_tasks_file()
    tasks = load_tasks()
    new_task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "date": datetime.now().isoformat(),
        "status": "TODO",
    }
    tasks.append(new_task)
    save_tasks(tasks)
    console.print(f"[green]Task added:[/] {new_task['description']}")


# Show a specific task
def show_task(task_id):
    ensure_tasks_file()
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task:
        table = Table(title="Task Details")
        table.add_column("Field", style="bold magenta")
        table.add_column("Value")
        table.add_row("ID", task["id"])
        table.add_row("Description", task["description"])
        table.add_row("Date", task["date"])
        table.add_row("Status", task["status"])
        console.print(table)
    else:
        console.print(f"[red]Task with ID {task_id} not found.[/]")


# List and toggle tasks interactively
def list_tasks():
    ensure_tasks_file()
    tasks = load_tasks()

    def render_task_list():
        table = Table(title="Tasks", box=None)
        table.add_column("[cyan]Done[/]")
        table.add_column("[bold magenta]ID[/]")
        table.add_column("[bold yellow]Description[/]")
        table.add_column("[bold green]Date[/]")

        for task in tasks:
            status = "[green]✓[/]" if task["status"] == "DONE" else "[red]✗[/]"
            table.add_row(status, task["id"], task["description"], task["date"])

        return Panel(Align.center(table), title="[bold white]Task List")

    with Live(render_task_list(), refresh_per_second=4) as live:
        while True:
            key = Prompt.ask(
                "Press [bold cyan]Space[/] to toggle, [bold red]q[/] to quit",
                default="q",
            )
            if key == "q":
                break
            elif key == "space":
                task_id = Prompt.ask("Enter task ID to toggle status")
                task = next((t for t in tasks if t["id"] == task_id), None)
                if task:
                    task["status"] = "DONE" if task["status"] == "TODO" else "TODO"
                    save_tasks(tasks)
                else:
                    console.print(f"[red]Task with ID {task_id} not found.[/]")


# Main CLI logic
def main():
    parser = argparse.ArgumentParser(description="Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Add task
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", type=str, help="Description of the task")

    # Show task
    show_parser = subparsers.add_parser("show", help="Show a task by ID")
    show_parser.add_argument("task_id", type=str, help="ID of the task")

    # List tasks
    list_parser = subparsers.add_parser("list", help="List and manage tasks")

    args = parser.parse_args()

    if args.command == "add":
        add_task(args.description)
    elif args.command == "show":
        show_task(args.task_id)
    elif args.command == "list":
        list_tasks()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
