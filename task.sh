#!/bin/bash
TASK_DIR=".project_tasks"
TASK_FILE="$TASK_DIR/tasks.json"

initialize() {
  [ ! -d "$TASK_DIR" ] && mkdir -p "$TASK_DIR"
  [ ! -f "$TASK_FILE" ] && echo "[]" > "$TASK_FILE"
}

add_task() {
  local task_name="$1"
  local task_description="$2"

  # Prompt for task name if not provided
  if [ -z "$task_name" ]; then
    task_name=$(gum input --placeholder "Enter the task name")
    if [ -z "$task_name" ]; then
      gum style --foreground 1 "Task name cannot be empty!"
      return
    fi
  fi

  # Prompt for task description if not provided
  if [ -z "$task_description" ]; then
    task_description=$(gum input --placeholder "Enter the task description")
    if [ -z "$task_description" ]; then
      gum style --foreground 1 "Task description cannot be empty!"
      return
    fi
  fi

  local task_id
  task_id=$(date +%s)
  local date_created
  date_created=$(date +"%Y-%m-%d %H:%M:%S")

  local new_task
  new_task=$(jq -n \
    --arg id "$task_id" \
    --arg name "$task_name" \
    --arg description "$task_description" \
    --arg date "$date_created" \
    '{id: $id, name: $name, description: $description, date: $date, status: "TODO"}')

  jq ". + [ $new_task ]" "$TASK_FILE" > "$TASK_FILE.tmp" && mv "$TASK_FILE.tmp" "$TASK_FILE"

  gum style --foreground 2 "Task \"$task_name\" added successfully!"
}

show_task() {
  local task_id="$1"

  if [ -z "$task_id" ]; then
    # No ID provided => let user pick one task to show
    local tasks
    tasks=$(jq -c \
      'sort_by(
         if .status == "TODO" then 0 else 1 end,
         .date
       )[]' \
      "$TASK_FILE")

    if [ -z "$tasks" ]; then
      gum style --foreground 1 "No tasks found!"
      return
    fi

    local choices=()
    local ids=()
    while IFS= read -r task; do
      local id name description status display
      id=$(echo "$task" | jq -r .id)
      name=$(echo "$task" | jq -r .name)
      description=$(echo "$task" | jq -r .description)
      status=$(echo "$task" | jq -r .status)
      [ "$status" == "DONE" ] && status="✅"
      [ "$status" == "TODO" ] && status="📝"
      display="$status $name"
      choices+=("$display")
      ids+=("$id")
    done < <(echo "$tasks")

    local selection
    selection=$(gum choose --header "Select a task to show details" "${choices[@]}")
    if [ -n "$selection" ]; then
      # Match the selection to an ID
      for i in "${!choices[@]}"; do
        if [[ "${choices[i]}" == "$selection" ]]; then
          task_id="${ids[i]}"
          break
        fi
      done
    else
      gum style --foreground 3 "No selection made. Exiting."
      return
    fi
  fi

  # Now show details for that ID
  local task
  task=$(jq ".[] | select(.id == \"$task_id\")" "$TASK_FILE")
  if [ -z "$task" ]; then
    gum style --foreground 1 "Task not found!"
    return
  fi

  gum format -- """
### Task Details

**ID**: $(echo "$task" | jq -r .id)
**Name**: $(echo "$task" | jq -r .name)
**Description**: $(echo "$task" | jq -r .description)
**Date Created**: $(echo "$task" | jq -r .date)
**Status**: $(echo "$task" | jq -r .status)
"""
}

list_tasks() {
  # Sorted: TODO first, then DONE, by date
  local tasks
  tasks=$(jq -c \
    'sort_by(
       if .status == "TODO" then 0 else 1 end,
       .date
     )[]' \
    "$TASK_FILE")

  if [ -z "$tasks" ]; then
    gum style --foreground 1 "No tasks found!"
    return
  fi

  local choices=()
  local ids=()
  while IFS= read -r task; do
    local id description status display
    id=$(echo "$task" | jq -r .id)
    # description=$(echo "$task" | jq -r .description)
    name=$(echo "$task" | jq -r .name)
    status=$(echo "$task" | jq -r .status)
    [ "$status" == "DONE" ] && status="✅"
    [ "$status" == "TODO" ] && status="📝"
    display="$status $name"
    choices+=("$display")
    ids+=("$id")
  done < <(echo "$tasks")

  # Choose multiple tasks to toggle
  local selections
  selections=$(gum choose --no-limit --header "Toggle task status with space; ENTER when done" "${choices[@]}")

  [ -z "$selections" ] && gum style --foreground 3 "No tasks selected. Exiting." && return

  # Update all selected tasks
  while IFS= read -r selected_display; do
    for i in "${!choices[@]}"; do
      if [[ "${choices[i]}" == "$selected_display" ]]; then
        local selected_id="${ids[i]}"
        jq "map(if .id == \"$selected_id\" then .status = (if .status == \"TODO\" then \"DONE\" else \"TODO\" end) else . end)" \
          "$TASK_FILE" > "$TASK_FILE.tmp" && mv "$TASK_FILE.tmp" "$TASK_FILE"
      fi
    done
  done <<< "$selections"

  gum style --foreground 2 "Task statuses updated!"
}

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
      echo "Usage: task {add <desc>|show [id]|list}" >&2
      exit 1
      ;;
  esac
}

dispatch "$@"

