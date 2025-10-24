const API_URL = 'http://127.0.0.1:8000';
let token = localStorage.getItem('token')

function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden', 'success', 'error');
    toast.classList.add(isError ? 'error' : 'success');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function updateUI(isLoggedIn) {
    document.getElementById('auth-section').classList.toggle('hidden', isLoggedIn);
    document.getElementById('dashboard-section').classList.toggle('hidden', !isLoggedIn);
    if (isLoggedIn) {
        checkBalance();
        loadTransactions();
    }
}

// Auth Functions
async function signup(event) {
    event.preventDefault();
    const name = document.getElementById('signup-name').value;
    const upi_id = document.getElementById('signup-upi').value;
    const password = document.getElementById('signup-password').value;

    try {
        const res = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, upi_id, password })
        });

        const data = await res.json();
        if (res.ok) {
            showToast('Account created successfully! Please login.');
            document.querySelector('[data-tab="login"]').click();
            event.target.reset();
        } else {
            throw new Error(data.detail || 'Signup failed');
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

async function login(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_URL}/token`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        if (res.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            showToast('Login successful');
            updateUI(true);
        } else {
            throw new Error(data.detail || 'Login failed');
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    updateUI(false);
    showToast('Logged out successfully');
}

// Transaction Functions
async function sendMoney(event) {
    event.preventDefault();
    const to_upi = document.getElementById('to-upi').value;
    const amount = parseFloat(document.getElementById('amount').value);

    try {
        const res = await fetch(`${API_URL}/me/send`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ to_upi, amount })
        });

        const data = await res.json();
        if (res.ok) {
            showToast(data.message);
            checkBalance();
            loadTransactions();
            event.target.reset();
        } else {
            throw new Error(data.detail || 'Transfer failed');
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

async function checkBalance() {
    try {
        const res = await fetch(`${API_URL}/me/balance`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (res.ok) {
            document.getElementById('balance-amount').textContent = 
                new Intl.NumberFormat('en-IN', { 
                    style: 'currency', 
                    currency: 'INR' 
                }).format(data.balance);
        } else {
            throw new Error(data.detail || 'Could not fetch balance');
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

async function loadTransactions() {
    try {
        const res = await fetch(`${API_URL}/me/transactions`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const transactions = await res.json();
        
        const list = document.getElementById('transactions-list');
        list.innerHTML = transactions.length ? '' : '<p>No transactions yet</p>';
        
        transactions.forEach(tx => {
            const item = document.createElement('div');
            item.className = 'transaction-item';
            item.innerHTML = `
                <div>
                    <strong>${tx.sender_upi === tx.receiver_upi ? 'Self Transfer' : 
                        tx.sender_upi}</strong> →
                    <strong>${tx.receiver_upi}</strong>
                </div>
                <div>
                    <strong>₹${tx.amount}</strong>
                    <div class="text-secondary">${new Date(tx.created_at).toLocaleDateString()}</div>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        showToast('Could not load transactions', true);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Auth tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.auth-form').forEach(form => {
                form.classList.toggle('hidden', form.id !== `${btn.dataset.tab}-form`);
            });
        });
    });

    // Form submissions
    document.getElementById('signup-form').addEventListener('submit', signup);
    document.getElementById('login-form').addEventListener('submit', login);
    document.getElementById('send-form').addEventListener('submit', sendMoney);
    
    // Other actions
    document.getElementById('refresh-balance').addEventListener('click', checkBalance);
    document.getElementById('logout').addEventListener('click', logout);

    // Check if already logged in
    updateUI(!!token);
});
