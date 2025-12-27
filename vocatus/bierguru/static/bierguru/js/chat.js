

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie("csrftoken");

const chatBox = document.getElementById("chat");
const input = document.getElementById("msg");
const sendBtn = document.getElementById("send");

function appendLine(who, text) {
  const p = document.createElement("p");
  p.textContent = `${who}: ${text}`;
  chatBox.appendChild(p);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  appendLine("Jij", message);
  input.value = "";
  sendBtn.disabled = true;

  try {
    const resp = await fetch("/bierguru/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ message }),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      appendLine("Fout", `HTTP ${resp.status}: ${errText}`);
      return;
    }

    const data = await resp.json();
    appendLine("Vocatus", data.answer || "(geen antwoord)");
  } catch (e) {
    appendLine("Fout", e.toString());
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
