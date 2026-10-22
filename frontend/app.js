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

  // Conversation history: all sessions live in one localStorage entry.
  var SESSIONS_KEY = "personal-ai-agent.sessions";
  var ACTIVE_KEY = "personal-ai-agent.activeSession";
  var DEFAULT_TITLE = "Nouvelle discussion";
  var TITLE_MAX_LENGTH = 40;

  var app = document.getElementById("app");
  var chat = document.getElementById("chat");
  var emptyTemplate = document.getElementById("empty-state").cloneNode(true);
  var composer = document.getElementById("composer");
  var input = document.getElementById("message");
  var sendButton = document.getElementById("send");
  var statusLine = document.getElementById("status");
  var urlInput = document.getElementById("backend-url");
  var saveUrlButton = document.getElementById("save-url");
  var newChatButton = document.getElementById("new-chat");
  var sessionList = document.getElementById("session-list");
  var sidebarToggle = document.getElementById("sidebar-toggle");

  var busy = false;
  var sessions = loadSessions();
  var activeId = null;

  function getBackendUrl() {
    var saved = window.localStorage.getItem(STORAGE_KEY);
    var url = saved || window.BACKEND_URL || DEFAULT_BACKEND_URL;
    return url.replace(/\/+$/, "");
  }

  function setStatus(text) {
    statusLine.textContent = text || "";
  }

  function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
  }

  /* ---------- Storage ---------- */

  function loadSessions() {
    try {
      var parsed = JSON.parse(window.localStorage.getItem(SESSIONS_KEY) || "[]");
      if (!Array.isArray(parsed)) return [];
      return parsed.filter(function (s) {
        return s && typeof s.id === "string" && Array.isArray(s.messages);
      });
    } catch (e) {
      return [];
    }
  }

  function saveSessions() {
    try {
      window.localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    } catch (e) {
      setStatus("Impossible d'enregistrer l'historique dans ce navigateur.");
    }
  }

  function setActiveId(id) {
    activeId = id;
    try {
      window.localStorage.setItem(ACTIVE_KEY, id);
    } catch (e) {
      // Persistence of the active session is best effort.
    }
  }

  function findSession(id) {
    for (var i = 0; i < sessions.length; i++) {
      if (sessions[i].id === id) return sessions[i];
    }
    return null;
  }

  function sortedSessions() {
    return sessions.slice().sort(function (a, b) {
      return b.updatedAt - a.updatedAt;
    });
  }

  function generateId() {
    return "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  }

  function createSession() {
    var now = Date.now();
    var session = {
      id: generateId(),
      title: DEFAULT_TITLE,
      createdAt: now,
      updatedAt: now,
      messages: []
    };
    sessions.push(session);
    return session;
  }

  function touch(session) {
    session.updatedAt = Date.now();
  }

  function titleFromText(text) {
    var clean = text.replace(/\s+/g, " ").trim();
    return clean.length > TITLE_MAX_LENGTH ? clean.slice(0, TITLE_MAX_LENGTH - 1) + "…" : clean;
  }

  function formatDate(ts) {
    try {
      return new Date(ts).toLocaleString("fr-FR", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch (e) {
      return "";
    }
  }

  /* ---------- Rendering ---------- */

  // All message text is inserted with textContent, never innerHTML, to avoid injection.
  function buildMessage(role, text) {
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
    return bubble;
  }

  // Placeholder shown while the agent works, with a generic activity badge.
  // The backend returns only the final reply, so individual tool calls are not listed.
  function buildThinking() {
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
    return bubble;
  }

  function renderChat() {
    chat.innerHTML = "";
    var session = findSession(activeId);
    if (!session || session.messages.length === 0) {
      chat.appendChild(emptyTemplate.cloneNode(true));
      return;
    }
    session.messages.forEach(function (m) {
      chat.appendChild(buildMessage(m.role, m.text));
    });
    scrollToBottom();
  }

  function renderSidebar() {
    sessionList.innerHTML = "";
    var list = sortedSessions();

    if (list.length === 0) {
      var none = document.createElement("li");
      none.className = "session-empty";
      none.textContent = "Aucune discussion";
      sessionList.appendChild(none);
      return;
    }

    list.forEach(function (session) {
      var item = document.createElement("li");
      item.className = "session-item" + (session.id === activeId ? " active" : "");

      var openButton = document.createElement("button");
      openButton.type = "button";
      openButton.className = "session-open";
      openButton.addEventListener("click", function () {
        switchSession(session.id);
      });

      var title = document.createElement("span");
      title.className = "session-title";
      title.textContent = session.title || DEFAULT_TITLE;

      var meta = document.createElement("span");
      meta.className = "session-meta";
      meta.textContent = formatDate(session.updatedAt);

      openButton.appendChild(title);
      openButton.appendChild(meta);

      var actions = document.createElement("div");
      actions.className = "session-actions";

      var renameButton = document.createElement("button");
      renameButton.type = "button";
      renameButton.className = "session-action";
      renameButton.title = "Renommer";
      renameButton.setAttribute("aria-label", "Renommer la discussion");
      renameButton.textContent = "\u270E";
      renameButton.addEventListener("click", function (event) {
        event.stopPropagation();
        renameSession(session.id);
      });

      var deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "session-action session-delete";
      deleteButton.title = "Supprimer";
      deleteButton.setAttribute("aria-label", "Supprimer la discussion");
      deleteButton.textContent = "\u00D7";
      deleteButton.addEventListener("click", function (event) {
        event.stopPropagation();
        deleteSession(session.id);
      });

      actions.appendChild(renameButton);
      actions.appendChild(deleteButton);
      item.appendChild(openButton);
      item.appendChild(actions);
      sessionList.appendChild(item);
    });
  }

  function setSidebarOpen(open) {
    app.classList.toggle("sidebar-open", open);
    sidebarToggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  /* ---------- Session actions ---------- */

  function switchSession(id) {
    if (!findSession(id)) return;
    setActiveId(id);
    setStatus("");
    renderChat();
    renderSidebar();
    setSidebarOpen(false);
  }

  function startNewSession() {
    var current = findSession(activeId);
    // Reuse the current session if it is still empty, to avoid piling up blank chats.
    if (!current || current.messages.length > 0) {
      var created = createSession();
      setActiveId(created.id);
      saveSessions();
    }
    setStatus("");
    renderChat();
    renderSidebar();
    setSidebarOpen(false);
    input.focus();
  }

  function deleteSession(id) {
    var session = findSession(id);
    if (!session) return;
    if (!window.confirm("Supprimer la discussion « " + session.title + " » ?")) return;

    sessions = sessions.filter(function (s) {
      return s.id !== id;
    });

    if (activeId === id) {
      var next = sortedSessions()[0] || createSession();
      setActiveId(next.id);
    }

    saveSessions();
    renderChat();
    renderSidebar();
  }

  function renameSession(id) {
    var session = findSession(id);
    if (!session) return;
    var name = window.prompt("Nouveau titre de la discussion", session.title);
    if (name === null) return;
    var clean = name.replace(/\s+/g, " ").trim();
    if (!clean) return;
    session.title = clean.slice(0, 80);
    saveSessions();
    renderSidebar();
  }

  /* ---------- Chat flow ---------- */

  function setBusy(state) {
    busy = state;
    sendButton.disabled = state;
    input.disabled = state;
  }

  // Writes the outcome into the session that sent the request, even if the user
  // has switched to another conversation in the meantime.
  function finishExchange(sessionId, role, text, placeholder) {
    if (placeholder && placeholder.parentNode) {
      placeholder.parentNode.removeChild(placeholder);
    }

    var session = findSession(sessionId);
    if (!session) return;

    if (role === "agent") {
      session.messages.push({ role: role, text: text });
      touch(session);
      saveSessions();
      renderSidebar();
    }

    if (sessionId === activeId) {
      chat.appendChild(buildMessage(role, text));
      scrollToBottom();
    }
  }

  function sendMessage(text) {
    var baseUrl = getBackendUrl();
    if (!baseUrl) {
      setStatus("Renseignez d'abord l'URL du backend dans Configuration.");
      urlInput.focus();
      return;
    }

    var session = findSession(activeId);
    if (!session) return;
    var sessionId = session.id;

    var isFirstUserMessage = !session.messages.some(function (m) {
      return m.role === "user";
    });
    session.messages.push({ role: "user", text: text });
    if (isFirstUserMessage && session.title === DEFAULT_TITLE) {
      session.title = titleFromText(text);
    }
    touch(session);
    saveSessions();

    renderChat();
    renderSidebar();
    var placeholder = buildThinking();
    chat.appendChild(placeholder);
    scrollToBottom();

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
        finishExchange(sessionId, "agent", reply, placeholder);
      })
      .catch(function (err) {
        var message = err && err.name === "AbortError"
          ? "La requête a dépassé le délai d'attente."
          : (err && err.message) || "Erreur réseau inconnue.";
        finishExchange(sessionId, "error", message, placeholder);
      })
      .then(function () {
        if (timer) clearTimeout(timer);
        setBusy(false);
        input.focus();
      });
  }

  /* ---------- Events ---------- */

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

  newChatButton.addEventListener("click", startNewSession);

  sidebarToggle.addEventListener("click", function () {
    setSidebarOpen(!app.classList.contains("sidebar-open"));
  });

  /* ---------- Init ---------- */

  function init() {
    var savedId = null;
    try {
      savedId = window.localStorage.getItem(ACTIVE_KEY);
    } catch (e) {
      savedId = null;
    }
    var session = findSession(savedId) || sortedSessions()[0] || createSession();
    setActiveId(session.id);
    saveSessions();
    renderChat();
    renderSidebar();
  }

  // Initialise the settings field with the effective URL.
  urlInput.value = getBackendUrl();
  if (!getBackendUrl()) {
    setStatus("Renseignez l'URL du backend dans Configuration pour commencer.");
  }

  init();
})();
