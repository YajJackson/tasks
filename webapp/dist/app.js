// API Base URL
const API_URL = '/api/tasks';

// DOM Elements
const taskTable = document.getElementById('task-tbody');
const emptyState = document.getElementById('empty-state');
const searchInput = document.getElementById('search-input');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

const addTaskMenuButton = document.getElementById('add-task-btn');
const createTaskModal = document.getElementById('create-task-modal');
const createTaskForm = document.getElementById('create-task-form');
const cancelCreateTaskButton = document.getElementById('cancel-create-task-modal-button');

const editTaskModal = document.getElementById('edit-task-modal');
const editTaskForm = document.getElementById('edit-task-form');
const cancelEditTaskButton = document.getElementById('cancel-edit-task-modal-button');

// Store all tasks globally
let allTasks = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
  setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
  addTaskMenuButton.addEventListener('click', () => {
    createTaskModal.style.display = 'flex';
  });

  cancelCreateTaskButton.addEventListener('click', () => {
    createTaskModal.style.display = 'none';
    createTaskForm.reset();
  });

  createTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await createTask();
  });

  editTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await updateTask();
  });

  cancelEditTaskButton.addEventListener('click', () => {
    editTaskModal.style.display = 'none';
    editTaskForm.reset();
  });

  // Search input listener
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value;
    const filteredTasks = filterTasks(allTasks, query);

    if (filteredTasks.length === 0) {
      taskTable.innerHTML = '';
      emptyState.style.display = 'block';
    } else {
      emptyState.style.display = 'none';
      renderTasks(filteredTasks);
    }
  });
}

// Load all tasks
async function loadTasks() {
  try {
    const response = await fetch(API_URL);
    const tasks = await response.json();

    // Store tasks globally
    allTasks = tasks;

    // Update progress bar
    updateProgress();

    // Apply current search filter
    const query = searchInput.value;
    const filteredTasks = filterTasks(allTasks, query);

    if (filteredTasks.length === 0) {
      taskTable.innerHTML = '';
      emptyState.style.display = 'block';
    } else {
      emptyState.style.display = 'none';
      renderTasks(filteredTasks);
    }
  } catch (error) {
    console.error('Error loading tasks:', error);
    alert('Failed to load tasks');
  }
}

// Render tasks in table
function renderTasks(tasks) {
  // Sort: TODO first, then by date descending
  const sortedTasks = tasks.sort((a, b) => {
    if (a.status !== b.status) {
      return a.status === 'TODO' ? -1 : 1;
    }
    return new Date(b.date) - new Date(a.date);
  });

  taskTable.innerHTML = sortedTasks.map((task, index) => `
        <tr class="${task.status === 'DONE' ? 'done' : ''}">
            <td>${index + 1}</td>
            <td>
                <span class="status-badge status-${task.status.toLowerCase()}">
                    ${task.status}
                </span>
            </td>
            <td class="task-name">${escapeHtml(task.name)}</td>
            <td class="task-description">${escapeHtml(task.description)}</td>
            <td class="task-date">${task.date}</td>
            <td class="actions">

              <ul role="menu-bar">
                <li role="menu-item" tabindex="0" aria-haspopup="true">
                  Actions
                  <ul role="menu">
                    <li role="menu-item" id="add-task-btn"><a href="#" onclick="openEditModal('${task.id}')">Edit</a></li>
                    <li role="menu-item" id="find-task-btn"><a href="#" onclick="deleteTask('${task.id}')">Delete</a></li>
                  </ul>
                </li>
              </ul>
            </td>
        </tr>
    `).join('');
}

// Create new task
async function createTask() {
  const name = document.getElementById('create-task-name').value.trim();
  const description = document.getElementById('create-task-description').value.trim();

  if (!name || !description) {
    alert('Both name and description are required');
    return;
  }

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, description }),
    });

    if (response.ok) {
      createTaskForm.reset();
      createTaskModal.style.display = 'none';
      await loadTasks();
    } else {
      const error = await response.json();
      alert(`Error: ${error.error || 'Failed to create task'}`);
    }
  } catch (error) {
    console.error('Error creating task:', error);
    alert('Failed to create task');
  }
}

// Open edit modal
async function openEditModal(taskId) {
  try {
    const response = await fetch(API_URL);
    const tasks = await response.json();
    const task = tasks.find(t => t.id === taskId);

    if (task) {
      document.getElementById('edit-task-id').value = task.id;
      document.getElementById('edit-task-name').value = task.name;
      document.getElementById('edit-task-description').value = task.description;
      document.getElementById('edit-task-status').value = task.status;
      editTaskModal.style.display = 'flex';
    }
  } catch (error) {
    console.error('Error loading task:', error);
    alert('Failed to load task');
  }
}

// Update task
async function updateTask() {
  const taskId = document.getElementById('edit-task-id').value;
  const name = document.getElementById('edit-task-name').value.trim();
  const description = document.getElementById('edit-task-description').value.trim();
  const status = document.getElementById('edit-task-status').value;

  if (!name || !description) {
    alert('Both name and description are required');
    return;
  }

  try {
    const response = await fetch(`${API_URL}/${taskId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, description, status }),
    });

    if (response.ok) {
      editTaskModal.style.display = 'none';
      editTaskForm.reset();
      await loadTasks();
    } else {
      const error = await response.json();
      alert(`Error: ${error.error || 'Failed to update task'}`);
    }
  } catch (error) {
    console.error('Error updating task:', error);
    alert('Failed to update task');
  }
}

// Delete task
async function deleteTask(taskId) {
  const message = `Are you sure you want to delete task: ${taskId}?`
  if (!confirm(message)) {
    return;
  }

  try {
    const response = await fetch(`${API_URL}/${taskId}`, {
      method: 'DELETE',
    });

    if (response.ok || response.status === 204) {
      await loadTasks();
    } else {
      const error = await response.json();
      alert(`Error: ${error.error || 'Failed to delete task'}`);
    }
  } catch (error) {
    console.error('Error deleting task:', error);
    alert('Failed to delete task');
  }
}

// Utility function to escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Update progress bar
function updateProgress() {
  const totalTasks = allTasks.length;
  const doneTasks = allTasks.filter(task => task.status === 'DONE').length;
  const percentage = totalTasks > 0 ? (doneTasks / totalTasks) * 100 : 0;

  progressBar.style.width = `${percentage}%`;
  progressText.textContent = `${doneTasks}/${totalTasks} Complete`;
}

// Filter tasks based on search query
function filterTasks(tasks, query) {
  if (!query || query.trim() === '') {
    return tasks;
  }

  const normalizedQuery = query.toLowerCase().trim();

  return tasks.filter(task => {
    const searchableText = `${task.name} ${task.description} ${task.status}`.toLowerCase();
    return searchableText.includes(normalizedQuery);
  });
}
