const API_BASE = 'http://127.0.0.1:8000';

function showMessage(msg, isError = false) {
    console[isError ? 'error' : 'log'](msg);
    const el = document.getElementById('message');
    if (el) {
        el.textContent = msg;
        el.style.color = isError ? 'red' : 'green';
    }
}

function getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

async function handleResponse(res) {
    const text = await res.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch (e) { /* not JSON */ }
    if (!res.ok) {
        const body = text || res.statusText;
        throw { status: res.status, body, parsed: data };
    }
    return data;
}

async function signup(event) {
    if (event) event.preventDefault();
    const username = (document.getElementById('signup-username') || {}).value || (document.getElementById('username') || {}).value;
    const password = (document.getElementById('signup-password') || {}).value || (document.getElementById('password') || {}).value;
    if (!username || !password) { showMessage('Username and password required', true); return; }

    try {
        const res = await fetch(`${API_BASE}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await handleResponse(res);
        showMessage('Signup successful');
        if (data && data.access_token) localStorage.setItem('authToken', data.access_token);
        console.log('signup response', data);
    } catch (err) {
        showMessage(`Signup failed (${err.status || 'network'}): ${err.body || err}`, true);
        console.error('Signup error detail:', err);
    }
}

async function login(event) {
    if (event) event.preventDefault();
    const username = (document.getElementById('login-username') || {}).value || (document.getElementById('username') || {}).value;
    const password = (document.getElementById('login-password') || {}).value || (document.getElementById('password') || {}).value;
    if (!username || !password) { showMessage('Username and password required', true); return; }

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await handleResponse(res);
        showMessage('Login successful');
        if (data && data.access_token) localStorage.setItem('authToken', data.access_token);
        else if (data && data.token) localStorage.setItem('authToken', data.token);
        console.log('login response', data);
    } catch (err) {
        showMessage(`Login failed (${err.status || 'network'}): ${err.body || err}`, true);
        console.error('Login error detail:', err);
    }
}

async function sendMoney(event) {
    if (event) event.preventDefault();
    const to = (document.getElementById('to') || {}).value;
    const amount = parseFloat((document.getElementById('amount') || {}).value);
    if (!to || !amount) { showMessage('Recipient and amount required', true); return; }

    try {
        const res = await fetch(`${API_BASE}/send`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ to, amount })
        });
        const data = await handleResponse(res);
        showMessage('Payment sent');
        console.log('send response', data);
    } catch (err) {
        showMessage(`Send failed (${err.status || 'network'}): ${err.body || err}`, true);
        console.error('Send error detail:', err);
    }
}

async function checkBalance(event) {
    if (event) event.preventDefault();
    const username = (document.getElementById('balance-username') || {}).value || localStorage.getItem('username');
    try {
        // try GET first, fallback to POST if server expects body
        let res = await fetch(`${API_BASE}/balance${username ? '?username=' + encodeURIComponent(username) : ''}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (res.status === 405 || res.status === 400) {
            res = await fetch(`${API_BASE}/balance`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ username })
            });
        }
        const data = await handleResponse(res);
        showMessage('Balance: ' + (data?.balance ?? JSON.stringify(data)));
        console.log('balance response', data);
    } catch (err) {
        showMessage(`Balance check failed (${err.status || 'network'}): ${err.body || err}`, true);
        console.error('Balance error detail:', err);
    }
}

function logout() {
    localStorage.removeItem('authToken');
    showMessage('Logged out');
}

// attach to DOM if elements exist
document.addEventListener('DOMContentLoaded', () => {
    const sForm = document.getElementById('signup-form') || document.getElementById('signup');
    if (sForm) sForm.addEventListener('submit', signup);

    const lForm = document.getElementById('login-form') || document.getElementById('login');
    if (lForm) lForm.addEventListener('submit', login);

    const sendForm = document.getElementById('send-form') || document.getElementById('send');
    if (sendForm) sendForm.addEventListener('submit', sendMoney);

    const balanceBtn = document.getElementById('check-balance') || document.getElementById('balance-btn');
    if (balanceBtn) balanceBtn.addEventListener('click', checkBalance);

    const logoutBtn = document.getElementById('logout');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
});