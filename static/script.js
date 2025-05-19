document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const resultBlock = document.querySelector(".result");

    if (form) {
        form.addEventListener("submit", function (e) {
            const question = form.querySelector('input[name="q"]').value;
            if (!question) return;

            e.preventDefault(); // Останавливаем отправку

            // Удаляем старый ответ
            if (resultBlock) resultBlock.remove();

            // Создаём анимацию ожидания
            const thinking = document.createElement("div");
            thinking.className = "thinking";
            thinking.innerHTML = "🔮 Шар размышляет...";
            form.parentElement.appendChild(thinking);

            // Подождём 2 секунды — потом отправим форму по-настоящему
            setTimeout(() => {
                form.submit();
            }, 2000);
        });
    }
});
