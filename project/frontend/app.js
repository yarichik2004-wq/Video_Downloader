function log(msg) {
    const el = document.getElementById("debugLog");
    if (el) el.innerText = msg;
    console.log(msg);
}

function initApp() {
    try {
        if (!window.Telegram || !window.Telegram.WebApp) {
            log("Жду загрузки Telegram SDK...");
            setTimeout(initApp, 200);
            return;
        }

        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        log("Telegram SDK готов!");

        const API_BASE = "https://videodownloader-production-7dbf.up.railway.app";
        const urlInput = document.getElementById("urlInput");
        const downloadBtn = document.getElementById("downloadBtn");
        const errorBubble = document.getElementById("errorBubble");
        const btnText = document.getElementById("btnText");
        const btnSpinner = document.getElementById("btnSpinner");

        // 1. Постоянная проверка ввода
        setInterval(() => {
            const val = urlInput.value.trim();
            if (val.length < 5) {
                downloadBtn.classList.add("hidden");
                errorBubble.classList.add("hidden");
                return;
            }

            const lowVal = val.toLowerCase();
            const isValid = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"].some(d => lowVal.includes(d));

            if (isValid) {
                downloadBtn.classList.remove("hidden");
                downloadBtn.style.display = "block";
                errorBubble.classList.add("hidden");
            } else {
                downloadBtn.classList.add("hidden");
                errorBubble.classList.remove("hidden");
            }
        }, 800);

        // 2. Логика нажатия на кнопку
        downloadBtn.addEventListener("click", async () => {
            const url = urlInput.value.trim();
            const user = tg.initDataUnsafe?.user;

            if (!user?.id) {
                alert("Ошибка: Запусти бота через Telegram");
                return;
            }

            // Визуальная загрузка
            downloadBtn.disabled = true;
            btnText.textContent = "Отправка...";
            btnSpinner.classList.remove("hidden");
            log("Отправляю запрос на сервер...");

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
                    alert("✅ Готово! Видео скоро придет в чат.");
                    urlInput.value = "";
                } else {
                    const errData = await response.json();
                    alert("❌ Ошибка: " + (errData.detail || "Сервер отклонил запрос"));
                }
            } catch (err) {
                log("Ошибка сети: " + err.message);
                alert("❌ Ошибка соединения с сервером");
            } finally {
                downloadBtn.disabled = false;
                btnText.textContent = "Скачать";
                btnSpinner.classList.add("hidden");
            }
        });

    } catch (e) {
        log("Критическая ошибка: " + e.message);
    }
}

// Поехали!
initApp();