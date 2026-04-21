const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_BASE = "https://videodownloader-production-7dbf.up.railway.app";

const urlInput = document.getElementById("urlInput");
const downloadBtn = document.getElementById("downloadBtn");
const errorBubble = document.getElementById("errorBubble");
const btnText = document.getElementById("btnText");
const btnSpinner = document.getElementById("btnSpinner");
const statusEl = document.getElementById("status");

// Улучшенная проверка ссылки
function checkUrl(str) {
    if (!str) return { valid: false, empty: true };
    
    const domains = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"];
    try {
        const url = new URL(str);
        const isValid = domains.some(d => url.hostname.includes(d));
        return { valid: isValid, empty: false };
    } catch (e) {
        return { valid: false, empty: false };
    }
}

// Главный обработчик ввода
function handleInput() {
    const val = urlInput.value.trim();
    const result = checkUrl(val);

    if (result.empty) {
        downloadBtn.classList.add("hidden");
        errorBubble.classList.add("hidden");
        return;
    }

    if (result.valid) {
        downloadBtn.classList.remove("hidden");
        errorBubble.classList.add("hidden");
    } else {
        downloadBtn.classList.add("hidden");
        errorBubble.classList.remove("hidden");
    }
}

// Слушаем и ввод, и вставку
urlInput.addEventListener("input", handleInput);
urlInput.addEventListener("paste", () => setTimeout(handleInput, 100));

// Клик по кнопке
downloadBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    const user = tg.initDataUnsafe?.user;

    if (!user?.id) {
        showStatus("❌ Ошибка: Откройте через Telegram", "error");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/download`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                url: url,
                user_id: user.id,
                init_data: tg.initData
            }),
        });

        if (response.ok) {
            tg.HapticFeedback?.notificationOccurred("success");
            showStatus("✅ Запрос отправлен! Видео придет в чат.", "success");
            urlInput.value = "";
            downloadBtn.classList.add("hidden");
        } else {
            const errorData = await response.json();
            showStatus(`❌ Ошибка: ${errorData.detail || "Сервер не смог обработать ссылку"}`, "error");
        }
    } catch (err) {
        showStatus("❌ Ошибка соединения с Railway", "error");
    } finally {
        setLoading(false);
    }
});

function setLoading(isLoading) {
    downloadBtn.disabled = isLoading;
    btnText.textContent = isLoading ? "Загрузка..." : "Скачать";
    btnSpinner.classList.toggle("hidden", !isLoading);
}

function showStatus(msg, type) {
    statusEl.textContent = msg;
    statusEl.className = `status ${type}`;
    statusEl.classList.remove("hidden");
    setTimeout(() => statusEl.classList.add("hidden"), 5000);
}