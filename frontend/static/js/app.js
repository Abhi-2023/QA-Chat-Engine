const API = "http://localhost:8001";

const state = {
    token: localStorage.getItem("nx_token") || "",
    email: localStorage.getItem("nx_email") || "",
    name: localStorage.getItem("nx_name") || "",
    convoId: null,
    messages: [],
    streaming: false,
    menuId: null,
    files: [],
};

const $ = (s) => document.querySelector(s);
const chatEl = $("#chat-messages");
const inputEl = $("#message-input");
const sendEl = $("#send-btn");
const errEl = $("#auth-error");

document.addEventListener("DOMContentLoaded", () => {
    initAuth();
    initChat();
    initFiles();
    initSidebar();
    document.addEventListener("click", () =>
        document.querySelectorAll(".dropdown-menu").forEach((m) => m.remove())
    );
    if (state.token) showApp();
});

// ═══════════ AUTH ═══════════
function initAuth() {
    document.querySelectorAll(".auth-tab").forEach((t) =>
        t.addEventListener("click", () => {
            document.querySelectorAll(".auth-tab").forEach((x) => x.classList.remove("active"));
            t.classList.add("active");
            const tab = t.dataset.tab;
            $("#login-form").classList.toggle("hidden", tab !== "login");
            $("#register-form").classList.toggle("hidden", tab !== "register");
            errEl.classList.add("hidden");
        })
    );
    $("#login-form").addEventListener("submit", (e) => {
        e.preventDefault();
        auth("login", { email: $("#login-email").value, password: $("#login-password").value });
    });
    $("#register-form").addEventListener("submit", (e) => {
        e.preventDefault();
        auth("register", {
            email: $("#register-email").value,
            password: $("#register-password").value,
            full_name: $("#register-name").value,
        });
    });
    $("#logout-btn").addEventListener("click", logout);
}

async function auth(type, body) {
    errEl.classList.add("hidden");
    try {
        const r = await fetch(`${API}/auth/${type}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const d = await r.json();
        if (!r.ok) return showErr(d.detail || "Auth failed");
        state.token = d.access_token;
        state.email = d.email;
        state.name = body.full_name || d.email.split("@")[0];
        localStorage.setItem("nx_token", state.token);
        localStorage.setItem("nx_email", state.email);
        localStorage.setItem("nx_name", state.name);
        showApp();
    } catch {
        showErr("Connection failed. Is the backend running?");
    }
}

function showErr(m) { errEl.textContent = m; errEl.classList.remove("hidden"); }

function showApp() {
    $("#auth-section").classList.add("hidden");
    $("#user-section").classList.remove("hidden");
    const n = state.name || state.email.split("@")[0];
    $("#user-avatar").textContent = n.substring(0, 2).toUpperCase();
    $("#user-name").textContent = n;
    loadConversations();
}

function logout() {
    state.token = state.email = state.name = "";
    state.convoId = null;
    state.messages = [];
    state.files = [];
    localStorage.removeItem("nx_token");
    localStorage.removeItem("nx_email");
    localStorage.removeItem("nx_name");
    $("#auth-section").classList.remove("hidden");
    $("#user-section").classList.add("hidden");
    $("#welcome-screen").classList.remove("hidden");
    $("#chat-container").classList.add("hidden");
    chatEl.innerHTML = "";
    updateFilePreview();
}

// ═══════════ CONVERSATIONS ═══════════
async function loadConversations() {
    try {
        const r = await fetch(`${API}/chat/conversations`, { headers: hdr() });
        if (!r.ok) return;
        const list = await r.json();
        const el = $("#history-list");
        el.innerHTML = "";
        list.forEach((c) => {
            const d = document.createElement("div");
            d.className = "history-item" + (c.id === state.convoId ? " active" : "");
            d.dataset.id = c.id;
            d.innerHTML = `
                <span class="history-title">${esc(c.title || "New chat")}</span>
                <button class="history-menu-btn" onclick="event.stopPropagation();toggleMenu('${c.id}',this)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
                </button>`;
            d.addEventListener("click", () => loadConvo(c.id));
            el.appendChild(d);
        });
    } catch (e) { console.error(e); }
}

async function loadConvo(id) {
    try {
        const r = await fetch(`${API}/chat/conversations/${id}/messages`, { headers: hdr() });
        if (!r.ok) return;
        const msgs = await r.json();
        state.convoId = id;
        state.messages = msgs.map((m) => ({ role: m.role, content: m.content }));
        renderAll();
        showChat();
        highlightConvo();
    } catch (e) { console.error(e); }
}

function highlightConvo() {
    document.querySelectorAll(".history-item").forEach((i) =>
        i.classList.toggle("active", i.dataset.id === state.convoId)
    );
}

function initSidebar() {
    $("#new-chat-btn").addEventListener("click", () => {
        state.convoId = null;
        state.messages = [];
        state.files = [];
        chatEl.innerHTML = "";
        $("#welcome-screen").classList.remove("hidden");
        $("#chat-container").classList.add("hidden");
        updateFilePreview();
        highlightConvo();
    });
}

function toggleMenu(id, btn) {
    document.querySelectorAll(".dropdown-menu").forEach((m) => m.remove());
    state.menuId = id;
    const dd = document.createElement("div");
    dd.className = "dropdown-menu";
    dd.innerHTML = `
        <button class="dropdown-item" onclick="openRename()">Rename</button>
        <button class="dropdown-item danger" onclick="openDelete()">Delete</button>`;
    btn.parentElement.appendChild(dd);
    event.stopPropagation();
}

function openRename() {
    document.querySelectorAll(".dropdown-menu").forEach((m) => m.remove());
    const t = document.querySelector(`.history-item[data-id="${state.menuId}"] .history-title`);
    $("#rename-input").value = t ? t.textContent : "";
    $("#rename-dialog").classList.remove("hidden");
    $("#rename-input").focus();
}
function closeRenameDialog() { $("#rename-dialog").classList.add("hidden"); }
async function submitRename() {
    const t = $("#rename-input").value.trim();
    if (!t) return;
    await fetch(`${API}/chat/conversations/${state.menuId}`, {
        method: "PATCH", headers: { ...hdr(), "Content-Type": "application/json" },
        body: JSON.stringify({ title: t }),
    });
    closeRenameDialog();
    loadConversations();
}

function openDelete() {
    document.querySelectorAll(".dropdown-menu").forEach((m) => m.remove());
    $("#delete-dialog").classList.remove("hidden");
}
function closeDeleteDialog() { $("#delete-dialog").classList.add("hidden"); }
async function submitDelete() {
    await fetch(`${API}/chat/conversations/${state.menuId}`, { method: "DELETE", headers: hdr() });
    closeDeleteDialog();
    if (state.convoId === state.menuId) {
        state.convoId = null;
        state.messages = [];
        chatEl.innerHTML = "";
        $("#welcome-screen").classList.remove("hidden");
        $("#chat-container").classList.add("hidden");
    }
    loadConversations();
}

// ═══════════ FILES ═══════════
function initFiles() {
    const fileInput = $("#file-input");
    $("#attach-btn").addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", async () => {
        for (const file of fileInput.files) {
            const formData = new FormData();
            formData.append("file", file);
            try {
                const r = await fetch(`${API}/file/upload`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${state.token}` },
                    body: formData,
                });
                if (!r.ok) {
                    const err = await r.json();
                    alert(err.detail || "Upload failed");
                    continue;
                }
                const data = await r.json();
                state.files.push({ id: data.file_id, name: file.name, type: file.type });
            } catch {
                alert("Upload failed. Is the backend running?");
            }
        }
        fileInput.value = "";
        updateFilePreview();
        updateSendBtn();
    });

    const main = $(".main-content");
    main.addEventListener("dragover", (e) => { e.preventDefault(); main.style.outline = "2px dashed var(--accent)"; });
    main.addEventListener("dragleave", () => { main.style.outline = "none"; });
    main.addEventListener("drop", (e) => {
        e.preventDefault();
        main.style.outline = "none";
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event("change"));
        }
    });
}

function updateFilePreview() {
    const container = $("#attached-files");
    if (state.files.length === 0) {
        container.classList.add("hidden");
        container.innerHTML = "";
        return;
    }
    container.classList.remove("hidden");
    container.innerHTML = state.files.map((f, i) => `
        <div class="file-chip">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            ${esc(f.name)}
            <button class="file-chip-remove" onclick="removeFile(${i})">×</button>
        </div>
    `).join("");
}

function removeFile(idx) {
    state.files.splice(idx, 1);
    updateFilePreview();
    updateSendBtn();
}

// ═══════════ CHAT ═══════════
function initChat() {
    inputEl.addEventListener("input", () => {
        inputEl.style.height = "auto";
        inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + "px";
        updateSendBtn();
    });
    inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!sendEl.disabled) send();
        }
    });
    sendEl.addEventListener("click", send);
}

function updateSendBtn() {
    sendEl.disabled = (!inputEl.value.trim() && state.files.length === 0) || state.streaming;
}

async function send() {
    const text = inputEl.value.trim();
    if ((!text && state.files.length === 0) || state.streaming) return;

    showChat();

    const fileNames = state.files.map((f) => f.name);
    const fileIds = state.files.map((f) => f.id);
    const displayText = text || `Uploaded: ${fileNames.join(", ")}`;

    state.messages.push({ role: "user", content: displayText });
    appendMsg("user", displayText, fileNames);

    inputEl.value = "";
    inputEl.style.height = "auto";
    state.files = [];
    updateFilePreview();
    sendEl.disabled = true;
    state.streaming = true;

    const aiEl = appendMsg("assistant", "");
    const bubble = aiEl.querySelector(".msg-bubble");
    bubble.classList.add("streaming-cursor");

    let full = "";

    try {
        const r = await fetch(`${API}/chat/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${state.token}` },
            body: JSON.stringify({
                message: text || `Please analyze the uploaded file(s): ${fileNames.join(", ")}`,
                conversation_id: state.convoId,
                file_ids: fileIds.length > 0 ? fileIds : undefined,
            }),
        });

        if (!r.ok) {
            bubble.textContent = "Error: " + (await r.text());
            bubble.classList.remove("streaming-cursor");
            state.streaming = false;
            return;
        }

        const reader = r.body.getReader();
        const dec = new TextDecoder();
        let buf = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });
            const lines = buf.split("\n");
            buf = lines.pop();
            for (const ln of lines) {
                const t = ln.trim();
                if (!t.startsWith("data:")) continue;
                const j = t.substring(5).trim();
                if (!j) continue;
                try {
                    const d = JSON.parse(j);
                    if (d.type === "token" && d.content) {
                        full += d.content;
                        bubble.innerHTML = md(full);
                    } else if (d.type === "done") {
                        if (d.conversation_id) state.convoId = d.conversation_id;
                    } else if (d.type === "error") {
                        bubble.textContent = "Error: " + d.content;
                    }
                } catch {}
            }
        }
    } catch {
        bubble.textContent = "Connection error. Is the backend running?";
    }

    bubble.classList.remove("streaming-cursor");
    state.messages.push({ role: "assistant", content: full });
    state.streaming = false;
    updateSendBtn();
    loadConversations();
}

// ═══════════ RENDER ═══════════
function appendMsg(role, content, files) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    const initials = role === "user"
        ? (state.name || state.email).substring(0, 2).toUpperCase()
        : "⚡";

    let fileHTML = "";
    if (files && files.length > 0) {
        fileHTML = files.map((f) => `
            <div class="msg-file">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                ${esc(f)}
            </div>`).join("");
    }

    div.innerHTML = `
        <div class="msg-avatar">${initials}</div>
        <div class="msg-bubble">${fileHTML}${content ? md(content) : '<div class="loading-dots"><span></span><span></span><span></span></div>'}</div>`;

    chatEl.appendChild(div);
    $("#chat-container").scrollTop = $("#chat-container").scrollHeight;
    return div;
}

function renderAll() {
    chatEl.innerHTML = "";
    state.messages.forEach((m) => {
        if (m.role === "user" || m.role === "assistant") appendMsg(m.role, m.content);
    });
}

function showChat() {
    $("#welcome-screen").classList.add("hidden");
    $("#chat-container").classList.remove("hidden");
}

function sendQuickMessage(t) { inputEl.value = t; updateSendBtn(); send(); }

// ═══════════ UTILS ═══════════
function hdr() { return { Authorization: `Bearer ${state.token}` }; }

function md(t) {
    let h = t;
    h = h.replace(/```(\w*)\n([\s\S]*?)```/g, (_, l, c) => `<pre><code>${esc(c.trim())}</code></pre>`);
    h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
    h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    h = h.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    h = h.replace(/\n\n/g, "</p><p>");
    h = h.replace(/\n/g, "<br>");
    return `<p>${h}</p>`;
}

function esc(s) {
    const m = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return s.replace(/[&<>"']/g, (c) => m[c]);
}