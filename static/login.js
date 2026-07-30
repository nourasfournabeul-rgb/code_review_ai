const form = document.getElementById("login-form");
const message = document.getElementById("message-login");

form.addEventListener("submit", async (event) => {

    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username,
            password
        })
    });

    const data = await response.json();

    if (response.ok) {

        sessionStorage.setItem("connecte", "true");

        window.location.href = "/";

    } else {

        message.textContent = data.detail;
    }

});