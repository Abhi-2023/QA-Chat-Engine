const API_URL = "http://localhost:8001";

const state = {
    token: localStorage.getItem("nexus_token") || "",
    email: localStorage.getItem("nexus_email") || "",
    fullName: localStorage.getItem("nexus_name") || "",
    conversationId: null,
    messages: [],
    isStreaming: false,
    currentMode: "chat",
    menuConvoId: null,
};

const $ = (sel) => document.querySelector(sel);
const chatMessages = $("#chat-messages");
const messageInput = $("#message-input");
const sendBtn = $("#send-btn");
const authError = $("#auth-error");

// ── Init ──
document.addEventListener("DOMContentLoaded", () => {
    setupAuthTabs();
    setupAuthForms();
    setupChatInput();
    setupModeSelector();
    setupNewChat();
    setupLogout();
    document.addEventListener("click", closeAllDropdowns);
    if (state.token) showLoggedInState();
});

// ── Auth ──
function setupAuthTabs() {
    document.querySelectorAll(".auth-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            const target = tab.dataset.tab;
            $("#login-form").classList.toggle("hidden", target !== "login");
            $("#register-form").classList.toggle("hidden", target !== "register");
            authError.classList.add("hidden");
        });
    });
}

function setupAuthForms() {
    $("#login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        await doAuth("login", {
            email: $("#login-email").value,
            password: $("#login-password").value,
        });
    });
    $("#register-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        await doAuth("register", {
            email: $("#register-email").value,
            password: $("#register-password").value,
            full_name: $("#register-name").value,
        });
    });
}

async function doAuth(type, body) {
    try {
        authError.classList.add("hidden");
        const res = await fetch(`${API_URL}/auth/${type}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) { showAuthError(data.detail || "Authentication failed"); return; }

        state.token = data.access_token;
        state.email = data.email;
        state.fullName = body.full_name || data.email.split("@")[0];
        localStorage.setItem("nexus_token", state.token);
        localStorage.setItem("nexus_email", state.email);
        localStorage.setItem("nexus_name", state.fullName);
        showLoggedInState();
    } catch (err) {
        showAuthError("Connection failed. Is the backend running?");
    }
}

function showAuthError(msg) {
    authError.textContent = msg;
    authError.classList.remove("hidden");
}

function showLoggedInState() {
    $("#auth-section").classList.add("hidden");
    $("#user-section").classList.remove("hidden");
    const name = state.fullName || state.email.split("@")[0];
    const initials = name.substring(0, 2).toUpperCase();
    $("#user-avatar").textContent = initials;
    $("#user-name").textContent = name;
    loadConversations();
}

function setupLogout() {
    $("#logout-btn").addEventListener("click", () => {
        state.token = "";
        state.email = "";
        state.fullName = "";
        state.conversationId = null;
        state.messages = [];
        localStorage.removeItem("nexus_token");
        localStorage.removeItem("nexus_email");
        localStorage.removeItem("nexus_name");
        $("#auth-section").classList.remove("hidden");
        $("#user-section").classList.add("hidden");
        $("#welcome-screen").classList.remove("hidden");
        $("#chat-container").classList.add("hidden");
        chatMessages.innerHTML = "";
    });
}

// ── Conversations ──
async function loadConversations() {
    try {
        const res = await fetch(`${API_URL}/chat/conversations`, {
            headers: { Authorization: `Bearer ${state.token}` },
        });
        if (!res.ok) return;
        const conversations = await res.json();
        const list = $("#history-list");
        list.innerHTML = "";
        conversations.forEach((c) => {
            const div = document.createElement("div");
            div.className = "history-item" + (c.id === state.conversationId ? " active" : "");
            div.dataset.id = c.id;
            div.innerHTML = `
                <span class="history-title">${escapeHtml(c.title || "New chat")}</span>
                <button class="history-menu-btn" onclick="event.stopPropagation(); toggleMenu('${c.id}', this)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
                </button>
            `;
            div.addEventListener("click", () => loadConversation(c.id));
            list.appendChild(div);
        });
    } catch (err) {
        console.error("Failed to load conversations:", err);
    }
}

async function loadConversation(id) {
    try {
        const res = await fetch(`${API_URL}/chat/conversations/${id}/messages`, {
            headers: { Authorization: `Bearer ${state.token}` },
        });
        if (!res.ok) return;
        const messages = await res.json();
        state.conversationId = id;
        state.messages = messages.map((m) => ({ role: m.role, content: m.content }));
        renderAllMessages();
        showChatView();
        highlightActiveConvo();
    } catch (err) {
        console.error("Failed to load messages:", err);
    }
}

function highlightActiveConvo() {
    document.querySelectorAll(".history-item").forEach((item) => {
        item.classList.toggle("active", item.dataset.id === state.conversationId);
    });
}

function setupNewChat() {
    $("#new-chat-btn").addEventListener("click", () => {
        state.conversationId = null;
        state.messages = [];
        chatMessages.innerHTML = "";
        $("#welcome-screen").classList.remove("hidden");
        $("#chat-container").classList.add("hidden");
        highlightActiveConvo();
    });
}

// ── Three-dot Menu ──
function toggleMenu(convoId, btnEl) {
    closeAllDropdowns();
    state.menuConvoId = convoId;
    const dropdown = document.createElement("div");
    dropdown.className = "dropdown-menu";
    dropdown.innerHTML = `
        <button class="dropdown-item" onclick="openRenameDialog()">Rename</button>
        <button class="dropdown-item danger" onclick="openDeleteDialog()">Delete</button>
    `;
    btnEl.parentElement.appendChild(dropdown);
}

function closeAllDropdowns() {
    document.querySelectorAll(".dropdown-menu").forEach((m) => m.remove());
}

// ── Rename ──
function openRenameDialog() {
    closeAllDropdowns();
    const titleEl = document.querySelector(`.history-item[data-id="${state.menuConvoId}"] .history-title`);
    $("#rename-input").value = titleEl ? titleEl.textContent : "";
    $("#rename-dialog").classList.remove("hidden");
    $("#rename-input").focus();
}

function closeRenameDialog() {
    $("#rename-dialog").classList.add("hidden");
}

async function submitRename() {
    const newTitle = $("#rename-input").value.trim();
    if (!newTitle) return;
    try {
        const res = await fetch(`${API_URL}/chat/conversations/${state.menuConvoId}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${state.token}`,
            },
            body: JSON.stringify({ title: newTitle }),
        });
        if (res.ok) {
            closeRenameDialog();
            loadConversations();
        }
    } catch (err) {
        console.error("Rename failed:", err);
    }
}

// ── Delete ──
function openDeleteDialog() {
    closeAllDropdowns();
    $("#delete-dialog").classList.remove("hidden");
}

function closeDeleteDialog() {
    $("#delete-dialog").classList.add("hidden");
}

async function submitDelete() {
    try {
        const res = await fetch(`${API_URL}/chat/conversations/${state.menuConvoId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${state.token}` },
        });
        if (res.ok) {
            closeDeleteDialog();
            if (state.conversationId === state.menuConvoId) {
                state.conversationId = null;
                state.messages = [];
                chatMessages.innerHTML = "";
                $("#welcome-screen").classList.remove("hidden");
                $("#chat-container").classList.add("hidden");
            }
            loadConversations();
        }
    } catch (err) {
        console.error("Delete failed:", err);
    }
}

// ── Chat Input ──
function setupChatInput() {
    messageInput.addEventListener("input", () => {
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + "px";
        sendBtn.disabled = !messageInput.value.trim() || state.isStreaming;
    });
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) sendMessage();
        }
    });
    sendBtn.addEventListener("click", sendMessage);
}

// ── Send Message ──
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || state.isStreaming) return;

    showChatView();
    state.messages.push({ role: "user", content: text });
    appendMessage("user", text);

    messageInput.value = "";
    messageInput.style.height = "auto";
    sendBtn.disabled = true;
    state.isStreaming = true;

    const aiMsgEl = appendMessage("assistant", "");
    const bubbleEl = aiMsgEl.querySelector(".msg-bubble");
    bubbleEl.classList.add("streaming-cursor");

    let fullResponse = "";

    try {
        const res = await fetch(`${API_URL}/chat/send`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${state.token}`,
            },
            body: JSON.stringify({
                message: text,
                conversation_id: state.conversationId,
            }),
        });

        if (!res.ok) {
            bubbleEl.textContent = "Error: " + (await res.text());
            bubbleEl.classList.remove("streaming-cursor");
            state.isStreaming = false;
            return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed.startsWith("data:")) continue;
                const jsonStr = trimmed.substring(5).trim();
                if (!jsonStr) continue;
                try {
                    const data = JSON.parse(jsonStr);
                    if (data.type === "token" && data.content) {
                        fullResponse += data.content;
                        bubbleEl.innerHTML = formatMarkdown(fullResponse);
                    } else if (data.type === "done") {
                        if (data.conversation_id) state.conversationId = data.conversation_id;
                    } else if (data.type === "error") {
                        bubbleEl.textContent = "Error: " + data.content;
                    }
                } catch (e) {}
            }
        }
    } catch (err) {
        bubbleEl.textContent = "Connection error. Is the backend running?";
    }

    bubbleEl.classList.remove("streaming-cursor");
    state.messages.push({ role: "assistant", content: fullResponse });
    state.isStreaming = false;
    sendBtn.disabled = !messageInput.value.trim();
    loadConversations();
}

// ── Render Messages ──
function appendMessage(role, content) {
    const div = document.createElement("div");
    div.className = `message ${role}`;

    const initials = role === "user"
        ? (state.fullName || state.email).substring(0, 2).toUpperCase()
        : "N";

    div.innerHTML = `
        <div class="msg-avatar">${initials}</div>
        <div class="msg-bubble">${content ? formatMarkdown(content) : '<div class="loading-dots"><span></span><span></span><span></span></div>'}</div>
    `;

    chatMessages.appendChild(div);
    $("#chat-container").scrollTop = $("#chat-container").scrollHeight;
    return div;
}

function renderAllMessages() {
    chatMessages.innerHTML = "";
    state.messages.forEach((msg) => {
        if (msg.role === "user" || msg.role === "assistant") {
            appendMessage(msg.role, msg.content);
        }
    });
}

function showChatView() {
    $("#welcome-screen").classList.add("hidden");
    $("#chat-container").classList.remove("hidden");
}

function sendQuickMessage(text) {
    messageInput.value = text;
    sendBtn.disabled = false;
    sendMessage();
}

// ── Mode Selector ──
function setupModeSelector() {
    document.querySelectorAll(".mode-item").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mode-item").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            state.currentMode = btn.dataset.mode;
        });
    });
}

// ── Markdown ──
function formatMarkdown(text) {
    let html = text;
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
        `<pre><code>${escapeHtml(code.trim())}</code></pre>`
    );
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/\n\n/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");
    return `<p>${html}</p>`;
}

function escapeHtml(str) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return str.replace(/[&<>"']/g, (c) => map[c]);
}
