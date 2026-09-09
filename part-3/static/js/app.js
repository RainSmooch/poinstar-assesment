// State Manajemen Aplikasi
let currentThreadId = localStorage.getItem("um_academic_thread") || `sesi-${Math.random().toString(36).substring(2, 8)}`;
localStorage.setItem("um_academic_thread", currentThreadId);

let isGenerating = false;
let messageHistory = [];

document.addEventListener("DOMContentLoaded", () => {
  updateThreadUI();
  loadThreadList();
  setupEventListeners();
});

function updateThreadUI() {
  const threadLabel = document.getElementById("active-thread-label");
  if (threadLabel) {
    threadLabel.textContent = currentThreadId;
  }
}

function setupEventListeners() {
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");

  // Kirim dengan Enter (Shift+Enter untuk baris baru)
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Auto-resize input textarea
  chatInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
    if (this.scrollHeight > 160) {
      this.style.overflowY = "auto";
    } else {
      this.style.overflowY = "hidden";
    }
  });

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message || isGenerating) return;

    chatInput.value = "";
    chatInput.style.height = "auto";
    sendMessage(message);
  });
}

function newChatSession() {
  currentThreadId = `sesi-${Math.random().toString(36).substring(2, 8)}`;
  localStorage.setItem("um_academic_thread", currentThreadId);
  updateThreadUI();
  
  // Kosongkan tampilan pesan dan tampilkan welcome hero
  const messagesContainer = document.getElementById("messages-container");
  messagesContainer.innerHTML = "";
  
  const hero = document.getElementById("welcome-hero");
  if (hero) hero.classList.remove("hidden");
  
  loadThreadList();
}

function switchThread(threadId) {
  if (isGenerating) return;
  currentThreadId = threadId;
  localStorage.setItem("um_academic_thread", currentThreadId);
  updateThreadUI();
  
  const messagesContainer = document.getElementById("messages-container");
  messagesContainer.innerHTML = "";
  
  const hero = document.getElementById("welcome-hero");
  if (hero) hero.classList.add("hidden");
  
  appendAssistantMessage(`*Membuka kembali riwayat percakapan sesi: **${threadId}**.* Silakan lanjutkan pertanyaan atau konsultasi naskah Anda.`);
  loadThreadList();
}

let threadToDelete = null;

function deleteThread(threadId) {
  if (isGenerating) return;
  
  // Siapkan dan tampilkan modal konfirmasi
  threadToDelete = threadId;
  const targetLabel = document.getElementById("delete-target-id");
  if (targetLabel) targetLabel.textContent = threadId;
  
  const modal = document.getElementById("delete-confirm-modal");
  if (modal) modal.classList.remove("hidden");
}

function closeDeleteConfirm() {
  const modal = document.getElementById("delete-confirm-modal");
  if (modal) modal.classList.add("hidden");
  threadToDelete = null;
}

async function executeDeleteThread() {
  if (!threadToDelete) return;
  const threadId = threadToDelete;
  closeDeleteConfirm();

  try {
    const res = await fetch(`/api/threads/${encodeURIComponent(threadId)}`, { method: "DELETE" });
    const data = await res.json();
    if (data.status === "ok") {
      if (threadId === currentThreadId) {
        newChatSession();
      } else {
        loadThreadList();
      }
      showAlert("success", "Sesi Berhasil Dihapus", `Sesi ${threadId} telah berhasil dihapus secara permanen.`);
    } else {
      showAlert("error", "Gagal Menghapus Sesi", data.message || "Kesalahan tidak diketahui.");
    }
  } catch (err) {
    console.error("Gagal menghapus thread:", err);
    showAlert("error", "Koneksi Terputus", "Gagal menghubungi server. Silakan coba kembali.");
  }
}

function showAlert(type, title, message) {
  const modal = document.getElementById("alert-modal");
  const titleEl = document.getElementById("alert-title");
  const msgEl = document.getElementById("alert-message");
  const iconContainer = document.getElementById("alert-icon-container");
  const border = document.getElementById("alert-border");
  
  if (!modal) return;

  titleEl.textContent = title;
  msgEl.textContent = message;

  if (type === "success") {
    border.className = "h-1.5 w-full bg-emerald-500";
    iconContainer.className = "mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-emerald-100 mb-4";
    iconContainer.innerHTML = `<svg class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
  } else {
    border.className = "h-1.5 w-full bg-red-500";
    iconContainer.className = "mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4";
    iconContainer.innerHTML = `<svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`;
  }

  modal.classList.remove("hidden");
}

function closeAlert() {
  const modal = document.getElementById("alert-modal");
  if (modal) modal.classList.add("hidden");
}

async function loadThreadList() {
  try {
    const res = await fetch("/api/threads");
    const data = await res.json();
    const container = document.getElementById("threads-list");
    if (!container) return;

    if (!data.threads || data.threads.length === 0) {
      container.innerHTML = `<div class="text-xs text-slate-400 px-3 py-2">Belum ada riwayat sesi lain.</div>`;
      return;
    }

    container.innerHTML = data.threads.map(tid => {
      const isActive = tid === currentThreadId;
      const activeClass = isActive ? "bg-[#F4FADC] text-[#16244D] font-bold border-l-4 border-[#ABD305]" : "text-slate-600 hover:bg-slate-100";
      return `
        <div class="flex items-center group ${activeClass} rounded-r transition">
          <button onclick="switchThread('${tid}')" class="flex-1 text-left text-xs px-3 py-2 truncate flex items-center gap-2">
            <svg class="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
            <span class="truncate">${tid}</span>
          </button>
          <button onclick="deleteThread('${tid}')" title="Hapus sesi ini" class="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 p-1.5 mr-1 rounded transition shrink-0">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
          </button>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Gagal memuat threads:", err);
  }
}

function sendQuickPrompt(promptText) {
  if (isGenerating) return;
  const chatInput = document.getElementById("chat-input");
  chatInput.value = promptText;
  document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

async function sendMessage(userMessage) {
  isGenerating = true;
  const hero = document.getElementById("welcome-hero");
  if (hero) hero.classList.add("hidden");

  // Tambahkan bubble user
  appendUserMessage(userMessage);

  // Buat bubble assistant kosong dengan kursor streaming
  const assistantBubble = createAssistantBubble();
  const contentDiv = assistantBubble.querySelector(".prose-content");
  contentDiv.classList.add("streaming-cursor");

  scrollToBottom();

  let accumulatedText = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        thread_id: currentThreadId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // simpan sisa baris belum lengkap

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const jsonStr = line.replace("data: ", "").trim();
          if (!jsonStr) continue;
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === "token") {
              accumulatedText += data.content;
              renderMarkdown(contentDiv, accumulatedText);
              scrollToBottom();
            } else if (data.type === "done") {
              if (data.thread_id) {
                currentThreadId = data.thread_id;
                localStorage.setItem("um_academic_thread", currentThreadId);
                updateThreadUI();
              }
            } else if (data.type === "error") {
              accumulatedText += `\n\n*${data.content}*`;
              renderMarkdown(contentDiv, accumulatedText);
            }
          } catch (e) {
            console.error("JSON parse error:", e, jsonStr);
          }
        }
      }
    }
  } catch (err) {
    console.error("Chat error:", err);
    accumulatedText += "\n\n*Mohon maaf, terjadi kendala saat menghubungi server AI. Silakan coba kembali.*";
    renderMarkdown(contentDiv, accumulatedText);
  } finally {
    isGenerating = false;
    contentDiv.classList.remove("streaming-cursor");
    renderMarkdown(contentDiv, accumulatedText);
    attachCopyButton(assistantBubble, accumulatedText);
    loadThreadList();
    scrollToBottom();
  }
}

function renderMarkdown(element, text) {
  if (window.marked) {
    element.innerHTML = window.marked.parse(text);
  } else {
    element.textContent = text;
  }
}

function appendUserMessage(text) {
  const container = document.getElementById("messages-container");
  const wrapper = document.createElement("div");
  wrapper.className = "flex justify-end mb-4 animate-fade-in";
  wrapper.innerHTML = `
    <div class="max-w-[85%] md:max-w-[70%] bg-gradient-to-r from-[#16244D] to-[#2A3D75] text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-sm border border-[#ABD305]/30">
      <div class="text-xs text-[#FFF500] font-bold mb-1">Anda</div>
      <div class="text-sm whitespace-pre-wrap leading-relaxed">${escapeHtml(text)}</div>
    </div>
  `;
  container.appendChild(wrapper);
}

function createAssistantBubble() {
  const container = document.getElementById("messages-container");
  const wrapper = document.createElement("div");
  wrapper.className = "flex justify-start mb-6 animate-fade-in group";
  wrapper.innerHTML = `
    <div class="flex gap-3 max-w-[95%] md:max-w-[85%]">
      <div class="w-9 h-9 rounded-full bg-white flex items-center justify-center p-0.5 shrink-0 shadow-md border-2 border-[#ABD305] overflow-hidden">
        <img src="/static/img/Lambang-UM.png" alt="UM" class="w-full h-full object-contain" />
      </div>
      <div class="flex-1 bg-white border border-slate-200/80 rounded-2xl rounded-tl-none p-4 shadow-sm hover:border-[#ABD305]/50 transition">
        <div class="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-[#16244D]">Asisten Karya Ilmiah UM</span>
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#F4FADC] text-[#3F6212] border border-[#D9F99D]">
              Pedoman 2017
            </span>
          </div>
          <div class="copy-action-slot"></div>
        </div>
        <div class="prose-content prose-academic text-sm text-slate-700 leading-relaxed"></div>
      </div>
    </div>
  `;
  container.appendChild(wrapper);
  return wrapper;
}

function appendAssistantMessage(markdownText) {
  const bubble = createAssistantBubble();
  const contentDiv = bubble.querySelector(".prose-content");
  renderMarkdown(contentDiv, markdownText);
  attachCopyButton(bubble, markdownText);
}

function attachCopyButton(bubble, textToCopy) {
  const slot = bubble.querySelector(".copy-action-slot");
  if (!slot) return;
  slot.innerHTML = `
    <button onclick="copyToClipboard(this, \`${escapeJsString(textToCopy)}\`)" class="text-slate-400 hover:text-sky-900 text-xs flex items-center gap-1 transition px-2 py-1 rounded hover:bg-slate-100">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
      <span>Salin</span>
    </button>
  `;
}

function copyToClipboard(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = `<span class="text-emerald-600 font-semibold">Tersalin!</span>`;
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  });
}

function scrollToBottom() {
  const chatScroll = document.getElementById("chat-scroll-area");
  if (chatScroll) {
    chatScroll.scrollTop = chatScroll.scrollHeight;
  }
}

function togglePedomanDrawer() {
  const drawer = document.getElementById("pedoman-drawer");
  if (drawer) {
    drawer.classList.toggle("translate-x-full");
  }
}

async function searchPedomanInDrawer() {
  const q = document.getElementById("drawer-search-input").value.trim();
  const resultsContainer = document.getElementById("drawer-search-results");
  if (!q) return;

  resultsContainer.innerHTML = `<div class="text-xs text-slate-500 py-4 text-center">Mencari dalam naskah pedoman...</div>`;

  try {
    const res = await fetch(`/api/pedoman/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.results || data.results.length === 0) {
      resultsContainer.innerHTML = `<div class="text-xs text-slate-500 py-4 text-center">Tidak ditemukan hasil untuk "${escapeHtml(q)}".</div>`;
      return;
    }

    resultsContainer.innerHTML = data.results.map(r => {
      const hlm = r.book_page ? `Hlm. ${r.book_page}` : `PDF p.${r.pdf_page}`;
      return `
        <div class="bg-white p-3 rounded-xl border border-slate-200 mb-2 shadow-sm hover:border-[#ABD305] transition">
          <div class="flex items-center justify-between text-xs font-bold text-[#16244D] mb-1">
            <span>${r.chapter}</span>
            <span class="bg-[#F4FADC] text-[#3F6212] border border-[#D9F99D] px-1.5 py-0.5 rounded text-[10px] font-semibold">${hlm}</span>
          </div>
          <p class="text-xs text-slate-600 line-clamp-3">${escapeHtml(r.text)}</p>
          <button onclick="sendQuickPrompt('Jelaskan lebih rinci mengenai ${escapeJsString(r.chapter)} (${hlm})')" class="mt-2 text-[11px] text-[#44599B] font-bold hover:underline">
            Tanyakan ke Asisten &rarr;
          </button>
        </div>
      `;
    }).join("");
  } catch (err) {
    resultsContainer.innerHTML = `<div class="text-xs text-red-500 py-2">Gagal memuat hasil pencarian.</div>`;
  }
}

function escapeHtml(string) {
  const entityMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return String(string).replace(/[&<>"']/g, s => entityMap[s]);
}

function escapeJsString(str) {
  return String(str).replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
}
