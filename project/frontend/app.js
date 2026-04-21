/**
 * 📁 frontend/app.js
 */

const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// !! ЗАМЕНИ НА СВОЙ URL !!
const API_BASE = "https://videodownloader-production-7dbf.up.railway.app";;

// ── DOM ──────────────────────────────────────────────────────────────────────
const urlInput     = document.getElementById("urlInput");
const pasteBtn     = document.getElementById("pasteBtn");
const downloadBtn  = document.getElementById("downloadBtn");
const btnText      = document.getElementById("btnText");
const btnSpinner   = document.getElementById("btnSpinner");
const statusEl     = document.getElementById("status");
const previewEl    = document.getElementById("preview");
const previewTitle = document.getElementById("previewTitle");
const previewDur   = document.getElementById("previewDuration");

let infoTimer = null;
let isLoading = false;

// ── Активация кнопки ──────────────────────────────────────────────────────────

function updateButtonState(url) {
  const valid = isValidUrl(url);
  downloadBtn.disabled = !valid;
  downloadBtn.style.opacity = valid ? "1" : "0.45";
}

// ── Вставка из буфера ─────────────────────────────────────────────────────────

pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      urlInput.value = text;
      handleUrlChange(text);
    }
  } catch {
    urlInput.focus();
  }
});

// ── Ввод / вставка ────────────────────────────────────────────────────────────

urlInput.addEventListener("input", (e) => {
  handleUrlChange(e.target.value.trim());
});

// Ловим Ctrl+V и долгое нажатие → Вставить
urlInput.addEventListener("paste", () => {
  setTimeout(() => handleUrlChange(urlInput.value.trim()), 50);
});

function handleUrlChange(url) {
  clearTimeout(infoTimer);
  hidePreview();
  hideStatus();
  updateButtonState(url);

  if (isValidUrl(url)) {
    infoTimer = setTimeout(() => fetchVideoInfo(url), 800);
  }
}

// ── Анимация кнопки ───────────────────────────────────────────────────────────

["mousedown", "touchstart"].forEach(evt =>
  downloadBtn.addEventListener(evt, () => {
    if (!downloadBtn.disabled) downloadBtn.style.transform = "scale(0.97)";
  }, { passive: true })
);
["mouseup", "touchend"].forEach(evt =>
  downloadBtn.addEventListener(evt, () => {
    downloadBtn.style.transform = "scale(1)";
  })
);

// ── Скачивание ────────────────────────────────────────────────────────────────
downloadBtn.addEventListener("click", async () => {
  alert("Кнопка нажата, URL: " + urlInput.value.trim()); // временно

  const url = urlInput.value.trim();
  if (!isValidUrl(url)) {
    showStatus("⚠️ Введи корректную ссылку", "error");
    return;
  }

  const user = tg.initDataUnsafe?.user;
  if (!user?.id) {
    showStatus("❌ Открой приложение из Telegram", "error");
    return;
  }

  setLoading(true);
  showStatus("⏳ Отправляю запрос...", "info");

  try {
    const res = await fetch(`${API_BASE}/api/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        user_id: user.id,
        init_data: tg.initData,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      showStatus(`❌ ${data.detail || "Ошибка сервера"}`, "error");
    } else {
      showStatus("✅ Готово! Видео скоро придёт в чат.", "success");
      urlInput.value = "";
      hidePreview();
      updateButtonState("");
      tg.HapticFeedback?.notificationOccurred("success");
    }
  } catch (err) {
    showStatus("❌ Нет соединения с сервером.", "error");
  } finally {
    setLoading(false);
  }
});

// ── Предпросмотр ──────────────────────────────────────────────────────────────

async function fetchVideoInfo(url) {
  try {
    const res = await fetch(`${API_BASE}/api/info`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!res.ok) return;
    const data = await res.json();
    previewTitle.textContent = data.title || "Видео";
    previewDur.textContent = data.duration ? `⏱ ${formatDuration(data.duration)}` : "";
    previewEl.classList.remove("hidden");
  } catch {
    // предпросмотр не критичен
  }
}

// ── Утилиты ───────────────────────────────────────────────────────────────────

function isValidUrl(str) {
  try {
    const url = new URL(str);
    return ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"].some(
      (d) => url.hostname.includes(d)
    );
  } catch {
    return false;
  }
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function setLoading(state) {
  isLoading = state;
  downloadBtn.disabled = state;
  btnText.textContent = state ? "Скачиваю..." : "Скачать";
  btnSpinner.classList.toggle("hidden", !state);
  downloadBtn.style.opacity = state ? "0.7" : "1";
}

function showStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className = `status ${type}`;
  statusEl.classList.remove("hidden");
}

function hideStatus() { statusEl.classList.add("hidden"); }
function hidePreview() { previewEl.classList.add("hidden"); }

// Кнопка изначально бледная
updateButtonState("");