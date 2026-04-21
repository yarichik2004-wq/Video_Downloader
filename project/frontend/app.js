// Функция для вывода логов прямо в приложении
function log(msg) {
    const el = document.getElementById("debugLog");
    if (el) el.innerText = msg;
    console.log(msg);
}

try {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    log("Telegram SDK готов");

    const API_BASE = "https://videodownloader-production-7dbf.up.railway.app";

    const urlInput = document.getElementById("urlInput");
    const downloadBtn = document.getElementById("downloadBtn");
    const errorBubble = document.getElementById("errorBubble");

    // Максимально простая проверка, которая никогда не выдаст ошибку
    function checkUrl(str) {
        if (!str || str.length < 5) return { valid: false, empty: true };
        const s = str.toLowerCase();
        const isValid = s.includes("youtube.com") || s.includes("youtu.be") || 
                        s.includes("tiktok.com") || s.includes("instagram.com");
        return { valid: isValid, empty: false };
    }

    function updateInterface() {
        const val = urlInput.value.trim();
        const res = checkUrl(val);
        
        log("Ввод: " + val.substring(0, 20) + "... Валидно: " + res.valid);

        if (res.empty) {
            downloadBtn.classList.add("hidden");
            errorBubble.classList.add("hidden");
        } else if (res.valid) {
            downloadBtn.classList.remove("hidden"); // Показываем кнопку
            downloadBtn.style.display = "block";    // На всякий случай принудительно
            errorBubble.classList.add("hidden");
        } else {
            downloadBtn.classList.add("hidden");
            errorBubble.classList.remove("hidden"); // Показываем "не удалось найти"
        }
    }

    // Слушаем всё подряд
    urlInput.addEventListener("input", updateInterface);
    urlInput.addEventListener("change", updateInterface);
    urlInput.addEventListener("blur", updateInterface);

    // Тот самый интервал, но с выводом лога
    setInterval(updateInterface, 1000);

    // Логика нажатия (без изменений, но в блоке try)
    downloadBtn.addEventListener("click", async () => {
        log("Нажата кнопка Скачать");
        const url = urlInput.value.trim();
        const user = tg.initDataUnsafe?.user;

        if (!user?.id) {
            alert("Запустите через бота!");
            return;
        }

        try {
            downloadBtn.disabled = true;
            const response = await fetch(`${API_BASE}/api/download`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, user_id: user.id, init_data: tg.initData }),
            });
            if (response.ok) alert("✅ Успешно!");
            else alert("❌ Ошибка сервера");
        } catch (e) {
            log("Ошибка Fetch: " + e.message);
        } finally {
            downloadBtn.disabled = false;
        }
    });

} catch (globalError) {
    log("КРИТИЧЕСКАЯ ОШИБКА: " + globalError.message);
}