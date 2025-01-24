#!/bin/bash

# Constants
TASK_DIR=".project_tasks"
TASK_FILE="$TASK_DIR/tasks.json"

# Ensure the task directory and file exist
initialize() {
  if [ ! -d "$TASK_DIR" ]; then
    mkdir "$TASK_DIR"
  fi

  if [ ! -f "$TASK_FILE" ]; then
    echo "[]" > "$TASK_FILE"
  fi
}

# Add a new task
add_task() {
  local task_description="$1"
  local task_id=$(date +%s)
  local date_created=$(date +"%Y-%m-%d %H:%M:%S")

  local new_task=$(jq -n \
    --arg id "$task_id" \
    --arg description "$task_description" \
    --arg date "$date_created" \
    '{id: $id, description: $description, date: $date, status: "TODO"}')

  jq ". + [ $new_task ]" "$TASK_FILE" > "$TASK_FILE.tmp" && mv "$TASK_FILE.tmp" "$TASK_FILE"

  gum style --foreground 2 "Task added successfully!"
}

# Show task details
show_task() {
  local task_id="$1"
  local task=$(jq ".[] | select(.id == \"$task_id\")" "$TASK_FILE")

  if [ -z "$task" ]; then
    gum style --foreground 1 "Task not found!"
    return
  fi

  gum format -- """
### Task Details

**ID**: $(echo "$task" | jq -r .id)
**Description**: $(echo "$task" | jq -r .description)
**Date Created**: $(echo "$task" | jq -r .date)
**Status**: $(echo "$task" | jq -r .status)
"""
}


# List tasks interactively
list_tasks() {
  local tasks
  tasks=$(jq -c ".[]" "$TASK_FILE")

  if [ -z "$tasks" ]; then
    gum style --foreground 1 "No tasks found!"
    return
  fi

  local choices=()
  local ids=()
  while IFS= read -r task; do
    local id description status display
    id=$(echo "$task" | jq -r .id)
    description=$(echo "$task" | jq -r .description)
    status=$(echo "$task" | jq -r .status)
    display="[$status] $description"
    choices+=("$display")
    ids+=("$id")
  done < <(echo "$tasks")

  # Capture selections line-by-line
  local selections
  selections=$(gum choose --no-limit --header "Toggle task status with spacebar:" "${choices[@]}")
  if [ -z "$selections" ]; then
    gum style --foreground 3 "No tasks selected. Exiting."
    return
  fi

  # Now process each selected line exactly
  while IFS= read -r selected_display; do
    for i in "${!choices[@]}"; do
      if [[ "${choices[i]}" == "$selected_display" ]]; then
        local selected_id="${ids[i]}"
        jq \
          "map(if .id == \"$selected_id\" then .status = (if .status == \"TODO\" then \"DONE\" else \"TODO\" end) else . end)" \
          "$TASK_FILE" > "$TASK_FILE.tmp" && mv "$TASK_FILE.tmp" "$TASK_FILE"
      fi
    done
  done <<< "$selections"

  gum style --foreground 2 "Task statuses updated!"
}



# Main function
dispatch() {
  initialize

  case "$1" in
    add)
      shift
      add_task "$@"
      ;;
    show)
      shift
      show_task "$1"
      ;;
    list)
      list_tasks
      ;;
    *)
      echo "Usage: $0 {add <task_description>|show <task_id>|list}" >&2
      exit 1
      ;;
  esac
}

dispatch "$@"

