const BASE_URL = "http://127.0.0.1:8000";

async function signup() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const upi_id = document.getElementById("upi").value;

    const res = await fetch(BASE_URL + "/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, upi_id })
    });
    const data = await res.json();
    alert(data.message || data.detail);
}

async function login() {
    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;

    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    const res = await fetch(BASE_URL + "/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params
    });
    const data = await res.json();
    alert(data.message || data.detail);
}

async function sendMoney() {
    const sender_upi = document.getElementById("sender").value;
    const receiver_upi = document.getElementById("receiver").value;
    const amount = parseFloat(document.getElementById("amount").value);

    const res = await fetch(BASE_URL + "/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender_upi, receiver_upi, amount })
    });
    const data = await res.json();
    alert(data.message || data.detail);
}

async function getBalance() {
    const upi_id = document.getElementById("checkUpi").value;
    const res = await fetch(BASE_URL + "/balance/" + upi_id);
    const data = await res.json();
    alert(`Balance: ₹${data.balance}`);
}
