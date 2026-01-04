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

const app = document.getElementById("app");
const endpoint = app?.dataset?.chatEndpoint || "/bierguru/chat/";

const chatBox = document.getElementById("chat");
const input = document.getElementById("msg");
const sendBtn = document.getElementById("send");
const statusEl = document.getElementById("status");

function setStatus(text = "") {
  if (statusEl) statusEl.textContent = text;
}

function isNearBottom(el) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 120;
}

function scrollToBottom(el) {
  el.scrollTop = el.scrollHeight;
}

function bubbleBase() {
  return "max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm sm:text-base leading-relaxed shadow-sm";
}

function appendBubble(role, text) {
  const shouldStick = isNearBottom(chatBox);

  const wrap = document.createElement("div");
  wrap.className = role === "user" ? "flex justify-end" : "flex justify-start";

  const bubble = document.createElement("div");
  if (role === "user") {
    bubble.className = bubbleBase() + " bg-brand-orange text-white";
  } else if (role === "error") {
    bubble.className = bubbleBase() + " bg-white border border-red-200 text-red-700";
  } else {
    bubble.className = bubbleBase() + " bg-white border border-black/10 text-brand-ink";
  }

  bubble.textContent = text; // veilig

  wrap.appendChild(bubble);
  chatBox.appendChild(wrap);

  if (shouldStick) scrollToBottom(chatBox);
}

function setDisabled(disabled) {
  sendBtn.disabled = disabled;
  input.disabled = disabled;
}

function autogrow(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  appendBubble("user", message);
  input.value = "";
  autogrow(input);

  setDisabled(true);
  setStatus("Bierguru typt…");

  try {
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ message }),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      appendBubble("error", `HTTP ${resp.status}: ${errText}`);
      return;
    }

    const data = await resp.json();
    appendBubble("assistant", data.answer || "(geen antwoord)");
  } catch (e) {
    appendBubble("error", e?.toString?.() || "Onbekende fout");
  } finally {
    setDisabled(false);
    setStatus("");
    input.focus();
  }
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("input", () => autogrow(input));

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// init
autogrow(input);
input.focus();
