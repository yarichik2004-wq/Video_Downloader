/**
 * 📁 frontend/app.js
 * Логика Telegram Mini App.
 */

// ── Инициализация Telegram WebApp ────────────────────────────────────────────

const tg = window.Telegram.WebApp;
tg.ready();       // сигнализируем Telegram что приложение загружено
tg.expand();      // раскрыть на всю высоту экрана

// URL бэкенда — подставь свой после деплоя
const API_BASE = "videodownloader-production-7dbf.up.railway.app";

// ── DOM-элементы ─────────────────────────────────────────────────────────────

const urlInput     = document.getElementById("urlInput");
const pasteBtn     = document.getElementById("pasteBtn");
const downloadBtn  = document.getElementById("downloadBtn");
const btnText      = document.getElementById("btnText");
const btnSpinner   = document.getElementById("btnSpinner");
const statusEl     = document.getElementById("status");
const previewEl    = document.getElementById("preview");
const previewTitle = document.getElementById("previewTitle");
const previewDur   = document.getElementById("previewDuration");

// ── Состояние ────────────────────────────────────────────────────────────────

let infoTimer = null;   // таймер для автозапроса инфо о видео
let isLoading = false;

// ── Вставка из буфера ─────────────────────────────────────────────────────────

pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    urlInput.value = text;
    urlInput.dispatchEvent(new Event("input"));
  } catch {
    // В Telegram WebApp clipboard API может быть недоступен
    urlInput.focus();
  }
});

// ── Обработка ввода URL ───────────────────────────────────────────────────────

urlInput.addEventListener("input", () => {
  const url = urlInput.value.trim();

  // Сбрасываем предыдущий таймер
  clearTimeout(infoTimer);
  hidePreview();
  hideStatus();

  if (isValidUrl(url)) {
    downloadBtn.disabled = false;
    // Через 800ms после последнего ввода — запрашиваем инфо о видео
    infoTimer = setTimeout(() => fetchVideoInfo(url), 800);
  } else {
    downloadBtn.disabled = true;
  }
});

// ── Кнопка «Скачать» ─────────────────────────────────────────────────────────

downloadBtn.addEventListener("click", async () => {
  if (isLoading) return;

  const url = urlInput.value.trim();
  if (!isValidUrl(url)) {
    showStatus("⚠️ Введи корректную ссылку", "error");
    return;
  }

  // Получаем user_id из Telegram WebApp
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
        init_data: tg.initData,   // для верификации на бэкенде
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      showStatus(`❌ ${data.detail || "Ошибка сервера"}`, "error");
    } else {
      showStatus("✅ Готово! Видео скоро придёт в чат.", "success");
      urlInput.value = "";
      hidePreview();
      downloadBtn.disabled = true;

      // Haptic feedback в Telegram
      tg.HapticFeedback?.notificationOccurred("success");
    }
  } catch (err) {
    showStatus("❌ Нет соединения с сервером", "error");
  } finally {
    setLoading(false);
  }
});

// ── Предпросмотр видео ────────────────────────────────────────────────────────

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
    previewDur.textContent   = data.duration
      ? `⏱ ${formatDuration(data.duration)}`
      : "";

    previewEl.classList.remove("hidden");
  } catch {
    // Тихо игнорируем — предпросмотр не критичен
  }
}

// ── Вспомогательные функции ───────────────────────────────────────────────────

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
}

function showStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className   = `status ${type}`;
  statusEl.classList.remove("hidden");
}

function hideStatus() {
  statusEl.classList.add("hidden");
}

function hidePreview() {
  previewEl.classList.add("hidden");
}
