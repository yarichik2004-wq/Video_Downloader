/**
 * 📁 frontend/app.js
 */

const API_BASE = "https://videodownloader-production-7dbf.up.railway.app";

// Ждём загрузки страницы и Telegram SDK
window.addEventListener("load", () => {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
  }

  const urlInput    = document.getElementById("urlInput");
  const downloadBtn = document.getElementById("downloadBtn");
  const btnText     = document.getElementById("btnText");
  const btnSpinner  = document.getElementById("btnSpinner");
  const statusEl    = document.getElementById("status");

  // ── Проверка URL ────────────────────────────────────────────────────────────

  function isValidUrl(str) {
    try {
      const url = new URL(str);
      return ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]
        .some(d => url.hostname.includes(d));
    } catch {
      return false;
    }
  }

  // ── Полинг поля — работает в любом браузере и Telegram WebApp ───────────────

  let lastValue = "";
  setInterval(() => {
    const val = urlInput.value.trim();
    if (val === lastValue) return;
    lastValue = val;

    const valid = isValidUrl(val);
    downloadBtn.disabled = !valid;
    downloadBtn.style.opacity = valid ? "1" : "0.45";

    if (!valid) hideStatus();
  }, 300);

  // ── Скачивание ──────────────────────────────────────────────────────────────

  downloadBtn.addEventListener("click", async () => {
    if (downloadBtn.disabled) return;

    const url = urlInput.value.trim();
    if (!isValidUrl(url)) {
      showStatus("⚠️ Введи корректную ссылку", "error");
      return;
    }

    const user = tg?.initDataUnsafe?.user;
    const userId = user?.id || tg?.initDataUnsafe?.user?.id || null;

    if (!userId) {
      // Для отладки — покажем что реально приходит от Telegram
      showStatus("Debug: " + JSON.stringify(tg?.initDataUnsafe), "error");
      return;
    }

    setLoading(true);
    showStatus("⏳ Скачиваю...", "info");

    try {
      const res = await fetch(`${API_BASE}/api/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          user_id: user.id,
          init_data: tg.initData || "",
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        showStatus(`❌ ${data.detail || "Ошибка сервера"}`, "error");
      } else {
        showStatus("✅ Готово! Видео скоро придёт в чат.", "success");
        urlInput.value = "";
        lastValue = "";
        downloadBtn.disabled = true;
        downloadBtn.style.opacity = "0.45";
        tg?.HapticFeedback?.notificationOccurred("success");
      }
    } catch (err) {
      showStatus("❌ Нет соединения с сервером.", "error");
    } finally {
      setLoading(false);
    }
  });

  // ── Утилиты ─────────────────────────────────────────────────────────────────

  function setLoading(state) {
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

  function hideStatus() {
    statusEl.classList.add("hidden");
  }

  // Кнопка изначально тусклая
  downloadBtn.disabled = true;
  downloadBtn.style.opacity = "0.45";
});