document.addEventListener('DOMContentLoaded', () => {
    // Determine page context based on DOM elements present
    const authForm = document.getElementById('authForm');
    const taskForm = document.getElementById('taskForm');

    // Handle Registration / Login
    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const isRegister = authForm.dataset.type === 'register';
            const endpoint = isRegister ? '/api/register' : '/api/login';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();

                if (!response.ok) throw new Error(data.error || 'Request failed');

                if (isRegister) {
                    alert('Account created! Please log in.');
                    window.location.href = '/login';
                } else {
                    window.location.href = '/dashboard';
                }
            } catch (err) {
                showAlert(err.message);
            }
        });
    }

    // Handle Dashboard Tasks
    if (taskForm) {
        fetchTasks();

        taskForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('taskInput');
            const title = input.value.trim();

            if (!title) return;

            try {
                const res = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title })
                });
                if (res.ok) {
                    input.value = '';
                    fetchTasks();
                }
            } catch (err) {
                console.error('Error adding task:', err);
            }
        });

        document.getElementById('logoutBtn').addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        });
    }
});

// Fetch all tasks for current user
async function fetchTasks() {
    const listElement = document.getElementById('taskList');
    try {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        
        listElement.innerHTML = '';
        tasks.forEach(task => {
            const li = document.createElement('li');
            li.className = `task-item ${task.completed ? 'completed' : ''}`;
            li.innerHTML = `
                <div class="task-info">
                    <input type="checkbox" ${task.completed ? 'checked' : ''} onchange="toggleTask(${task.id}, this.checked)">
                    <span class="task-title">${escapeHTML(task.title)}</span>
                </div>
                <button class="btn btn-danger" onclick="deleteTask(${task.id})">Delete</button>
            `;
            listElement.appendChild(li);
        });
    } catch (err) {
        console.error('Failed to load tasks:', err);
    }
}

// Toggle Task Completion State
async function toggleTask(id, completed) {
    await fetch(`/api/tasks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed })
    });
    fetchTasks();
}

// Delete Task
async function deleteTask(id) {
    await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
    fetchTasks();
}

function showAlert(message) {
    const alertBox = document.getElementById('alertBox');
    if (alertBox) {
        alertBox.textContent = message;
        alertBox.style.display = 'block';
    }
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag));
}