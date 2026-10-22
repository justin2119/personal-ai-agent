(function () {
  "use strict";

  // Backend URL resolution order:
  // 1. value saved in this browser (localStorage, set from the settings panel)
  // 2. window.BACKEND_URL defined in a config script (optional, e.g. config.js)
  // 3. default: http://127.0.0.1:8000
  var STORAGE_KEY = "personal-ai-agent.backendUrl";
  var DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
  var CHAT_PATH = "/api/chat";
  var REQUEST_TIMEOUT_MS = 120000;

  var chat = document.getElementById("chat");
  var emptyState = document.getElementById("empty-state");
  var composer = document.getElementById("composer");
  var input = document.getElementById("message");
  var sendButton = document.getElementById("send");
  var statusLine = document.getElementById("status");
  var urlInput = document.getElementById("backend-url");
  var saveUrlButton = document.getElementById("save-url");

  var busy = false;

  function getBackendUrl() {
    var saved = window.localStorage.getItem(STORAGE_KEY);
    var url = saved || window.BACKEND_URL || DEFAULT_BACKEND_URL;
    return url.replace(/\/+$/, "");
  }

  function setStatus(text) {
    statusLine.textContent = text || "";
  }

  function hideEmptyState() {
    if (emptyState && emptyState.parentNode) {
      emptyState.parentNode.removeChild(emptyState);
      emptyState = null;
    }
  }

  function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
  }

  // All message text is inserted with textContent, never innerHTML, to avoid injection.
  function addMessage(role, text) {
    hideEmptyState();
    var bubble = document.createElement("div");
    bubble.className = "message " + role;

    var label = document.createElement("span");
    label.className = "message-label";
    label.textContent = role === "user" ? "Vous" : role === "error" ? "Erreur" : "Agent";

    var body = document.createElement("div");
    body.className = "message-body";
    body.textContent = text;

    bubble.appendChild(label);
    bubble.appendChild(body);
    chat.appendChild(bubble);
    scrollToBottom();
    return bubble;
  }

  // Placeholder shown while the agent works, with a generic activity badge.
  // The backend returns only the final reply, so individual tool calls are not listed.
  function addThinking() {
    hideEmptyState();
    var bubble = document.createElement("div");
    bubble.className = "message agent thinking-bubble";

    var label = document.createElement("span");
    label.className = "message-label";
    label.textContent = "Agent";

    var row = document.createElement("div");
    row.className = "thinking";

    var dots = document.createElement("span");
    dots.className = "dots";
    for (var i = 0; i < 3; i++) {
      dots.appendChild(document.createElement("span"));
    }

    var badge = document.createElement("span");
    badge.className = "tool-badge";
    badge.textContent = "Réflexion et outils en cours";

    row.appendChild(dots);
    row.appendChild(badge);
    bubble.appendChild(label);
    bubble.appendChild(row);
    chat.appendChild(bubble);
    scrollToBottom();
    return bubble;
  }

  function setBusy(state) {
    busy = state;
    sendButton.disabled = state;
    input.disabled = state;
  }

  function sendMessage(text) {
    var baseUrl = getBackendUrl();
    if (!baseUrl) {
      setStatus("Renseignez d'abord l'URL du backend dans Configuration.");
      urlInput.focus();
      return;
    }

    addMessage("user", text);
    var placeholder = addThinking();
    setBusy(true);
    setStatus("");

    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS) : null;

    fetch(baseUrl + CHAT_PATH, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ message: text }),
      signal: controller ? controller.signal : undefined
    })
      .then(function (response) {
        return response.text().then(function (raw) {
          var data = null;
          try {
            data = raw ? JSON.parse(raw) : null;
          } catch (e) {
            data = null;
          }
          if (!response.ok) {
            var detail = data && (data.detail || data.error) ? (data.detail || data.error) : raw;
            throw new Error("Le backend a répondu " + response.status + ". " + (typeof detail === "string" ? detail : JSON.stringify(detail)));
          }
          if (!data || typeof data.reply !== "string") {
            throw new Error("Réponse inattendue du backend (champ reply manquant).");
          }
          return data.reply;
        });
      })
      .then(function (reply) {
        placeholder.parentNode.removeChild(placeholder);
        addMessage("agent", reply);
      })
      .catch(function (err) {
        placeholder.parentNode.removeChild(placeholder);
        var message = err && err.name === "AbortError"
          ? "La requête a dépassé le délai d'attente."
          : (err && err.message) || "Erreur réseau inconnue.";
        var bubble = addMessage("error", message);
        bubble.classList.add("error");
      })
      .then(function () {
        if (timer) clearTimeout(timer);
        setBusy(false);
        input.focus();
      });
  }

  composer.addEventListener("submit", function (event) {
    event.preventDefault();
    if (busy) return;
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    autoResize();
    sendMessage(text);
  });

  // Enter sends, Shift+Enter inserts a line break.
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      composer.requestSubmit ? composer.requestSubmit() : composer.dispatchEvent(new Event("submit", { cancelable: true }));
    }
  });

  function autoResize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  }
  input.addEventListener("input", autoResize);

  saveUrlButton.addEventListener("click", function () {
    var value = urlInput.value.trim().replace(/\/+$/, "");
    if (value && !/^https?:\/\//i.test(value)) {
      setStatus("L'URL doit commencer par http:// ou https://");
      return;
    }
    if (value) {
      window.localStorage.setItem(STORAGE_KEY, value);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    setStatus(value ? "URL du backend enregistrée." : "URL du backend effacée.");
  });

  // Initialise the settings field with the effective URL.
  urlInput.value = getBackendUrl();
  if (!getBackendUrl()) {
    setStatus("Renseignez l'URL du backend dans Configuration pour commencer.");
  }
})();
