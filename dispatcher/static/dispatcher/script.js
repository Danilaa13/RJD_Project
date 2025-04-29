const { DateTime, Duration } = luxon; // Убедимся, что Luxon загружен

    // --- Код для таймеров (из вашего примера) ---
    const updateTimers = () => {
        document.querySelectorAll('.timer').forEach(timer => {
            if (!timer.dataset.deadline) return; // Пропускаем, если нет дедлайна
            const deadline = DateTime.fromISO(timer.dataset.deadline);
            const now = DateTime.now();
            const timeValueSpan = timer.querySelector('.time-value');

            if (!timeValueSpan) return; // Пропускаем, если нет элемента для времени

            if (deadline <= now) {
                timeValueSpan.textContent = 'Просрочено';
                timer.classList.remove('normal', 'warning');
                timer.classList.add('urgent'); // Класс для стиля просрочено
                return;
            }

            const diff = deadline.diff(now, ['days', 'hours', 'minutes', 'seconds']).toObject(); // Добавил секунды для точности

            let timeString = '';
             if (diff.days > 0) {
                timeString += `${Math.floor(diff.days)}д `;
            }
            if (diff.hours > 0 || diff.days > 0) { // Показываем часы, если есть дни или часы
                 timeString += `${Math.floor(diff.hours)}ч `;
             }
            timeString += `${Math.floor(diff.minutes)}м`; // Всегда показываем минуты

            timeValueSpan.textContent = timeString.trim(); // Убираем лишние пробелы

            // Update color based on urgency
            const totalMinutes = (diff.days * 24 * 60) + (diff.hours * 60) + diff.minutes;
            timer.classList.remove('normal', 'warning', 'urgent'); // Сначала убираем все классы
            if (totalMinutes < 60) { // Менее часа
                timer.classList.add('urgent');
            } else if (totalMinutes < (6 * 60)) { // Менее 6 часов
                timer.classList.add('warning');
            } else { // Больше 6 часов
                timer.classList.add('normal');
            }
        });
    };
    setInterval(updateTimers, 30000); // Обновляем каждые 30 секунд
    updateTimers(); // Initial update

    // --- Код для фильтрации и поиска (из вашего примера) ---
    const searchInput = document.getElementById('search');
    const filterSelect = document.getElementById('filter');
    const taskList = document.getElementById('task-list');

    function filterTasks() {
        const searchText = searchInput.value.toLowerCase();
        const filter = filterSelect.value;

        taskList.querySelectorAll('.task-card').forEach(card => {
            // Проверяем текст ИЛИ данные в атрибутах для поиска
            const fio = card.querySelector('.task-title')?.textContent.toLowerCase() || '';
            const train = card.querySelector('.fa-train')?.nextElementSibling?.textContent.toLowerCase() || '';
            const wagon = card.querySelector('.fa-box')?.nextElementSibling?.textContent.toLowerCase() || '';
            const code = card.querySelector('.fa-exclamation-triangle')?.nextElementSibling?.textContent.toLowerCase() || '';
            const cardTextContent = card.textContent.toLowerCase(); // Общее содержимое

            const searchableText = `${fio} ${train} ${wagon} ${code} ${cardTextContent}`;

            const status = card.dataset.status;

            const matchesSearch = searchText === '' || searchableText.includes(searchText);
            const matchesFilter = filter === 'all' || status === filter;

            card.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
        });
    }
    searchInput.addEventListener('input', filterTasks);
    filterSelect.addEventListener('change', filterTasks);

    // --- Код для эффектов hover и нажатия кнопок (из вашего примера) ---
     taskList.querySelectorAll('.task-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-3px)';
            card.style.boxShadow = '0 8px 20px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.boxShadow = ''; // Вернуть дефолтный (или задать его в CSS)
        });
    });

     taskList.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mousedown', () => btn.style.transform = 'translateY(1px)');
        btn.addEventListener('mouseup', () => btn.style.transform = '');
        btn.addEventListener('mouseleave', () => btn.style.transform = '');
    });

    // --- НОВЫЙ КОД: Обработка кнопок смены статуса ---
    taskList.addEventListener('click', async (event) => {
        // Ищем ближайшую кнопку с классом btn-status-update
        const button = event.target.closest('.btn-status-update');
        if (!button) return; // Клик не по кнопке смены статуса

        const card = button.closest('.task-card');
        const requestId = card.dataset.requestId;
        const newStatus = button.dataset.newStatus;

        if (!requestId || !newStatus) return; // Нет ID заявки или нового статуса

        const url = `/api/request/${requestId}/update_status/`; // URL для обновления

        // Получаем CSRF токен (функция getCookie есть в script.js формы)
        function getCookie(name) { /* ... код функции getCookie ... */
             let cookieValue = null; if (document.cookie && document.cookie !== '') { const cookies = document.cookie.split(';'); for (let i = 0; i < cookies.length; i++) { const cookie = cookies[i].trim(); if (cookie.substring(0, name.length + 1) === (name + '=')) { cookieValue = decodeURIComponent(cookie.substring(name.length + 1)); break; } } } return cookieValue;
        }
        const csrftoken = getCookie('csrftoken');

        try {
             button.disabled = true; // Блокируем кнопку на время запроса
             const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrftoken && {'X-CSRFToken': csrftoken})
                },
                body: JSON.stringify({ status: newStatus })
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                // Обновляем статус на карточке БЕЗ перезагрузки страницы
                card.dataset.status = newStatus; // Обновляем data-атрибут
                // Обновляем текст статуса
                const statusTextMap = { 'new': 'Новая', 'assigned': 'В наряде', 'done': 'Выполнено', 'urgent': 'Срочная' };
                const statusElement = card.querySelector('.task-status');
                if(statusElement) {
                    statusElement.textContent = statusTextMap[newStatus] || newStatus;
                    // Обновляем класс для цвета
                    statusElement.className = `task-status status-${newStatus}`;
                }

                // Пере-блокируем/разблокируем кнопки на карточке
                card.querySelectorAll('.btn-status-update').forEach(btn => {
                    const btnStatus = btn.dataset.newStatus;
                    btn.disabled = (newStatus === 'done' || newStatus === btnStatus || (newStatus === 'assigned' && btnStatus === 'new'));
                     // Можно добавить более сложную логику блокировки если нужно
                });

                 // Если статус 'done', убираем таймер или меняем его текст
                const timerElement = card.querySelector('.timer');
                if (newStatus === 'done' && timerElement) {
                     timerElement.closest('.task-info').innerHTML = `<span class="label"><i class="fas fa-check-circle"></i> Статус:</span><span class="value status-done-text">Ремонт завершен</span>`; // Заменяем блок таймера
                 }

                // Обновить счетчики статистики (опционально, требует доп. логики)
                // filterTasks(); // Применить фильтр заново, если нужно скрыть/показать карточку

                console.log(result.message); // Лог успеха

            } else {
                 alert(`Ошибка обновления статуса: ${result.message || 'Неизвестная ошибка'}`);
                 button.disabled = false; // Разблокируем кнопку при ошибке
            }

        } catch (error) {
            console.error('Ошибка сети при обновлении статуса:', error);
            alert('Произошла ошибка при обновлении статуса.');
            button.disabled = false; // Разблокируем кнопку при ошибке сети
        }
    });