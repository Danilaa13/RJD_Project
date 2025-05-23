// Убедимся, что Luxon загружен глобально (как в вашем шаблоне)
const { DateTime, Duration } = luxon;

// --- Функция для получения CSRF куки (перемещена наверх) ---
// Эта функция была внутри обработчика клика, лучше определить ее один раз.
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// --- Код для таймеров ---
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

        const diff = deadline.diff(now, ['days', 'hours', 'minutes', 'seconds']).toObject();

        let timeString = '';
         if (diff.days > 0) {
            timeString += `${Math.floor(diff.days)}д `;
        }
        // Показываем часы, если есть дни или часы > 0
        if (diff.hours > 0 || diff.days > 0) {
             timeString += `${Math.floor(diff.hours)}ч `;
         }
         // Показываем минуты, если есть часы или минуты > 0, или если это единственная единица
         if (diff.minutes > 0 || diff.hours > 0 || diff.days > 0 || timeString === '') {
             timeString += `${Math.floor(diff.minutes)}м`;
         }


        timeValueSpan.textContent = timeString.trim();

        // Update color based on urgency
        const totalMinutes = (diff.days * 24 * 60) + (diff.hours * 60) + diff.minutes;
        timer.classList.remove('normal', 'warning', 'urgent');
        if (totalMinutes < 60) { // Менее часа
            timer.classList.add('urgent');
        } else if (totalMinutes < (6 * 60)) { // Менее 6 часов
            timer.classList.add('warning');
        } else { // Больше 6 часов
            timer.classList.add('normal');
        }
    });
};

// !!! Запускаем обновление таймеров только после загрузки DOM !!!
// setInterval(updateTimers, 30000);
// updateTimers();


// --- Код для фильтрации и поиска ---
const searchInput = document.getElementById('search');
const filterSelect = document.getElementById('filter');
const taskListElement = document.getElementById('task-list'); // Используем taskListElement для единообразия

function filterTasks() {
    const searchText = searchInput.value.toLowerCase();
    const filter = filterSelect.value;

    taskListElement.querySelectorAll('.task-card').forEach(card => {
        // Проверяем текст ИЛИ данные в атрибутах для поиска
        const fio = card.querySelector('.task-title')?.textContent.toLowerCase() || '';
        const tabel = card.querySelector('.fa-hashtag')?.nextElementSibling?.textContent.toLowerCase() || ''; // Поле Табельный номер
        const city = card.querySelector('.fa-city')?.nextElementSibling?.textContent.toLowerCase() || ''; // Поле Город отпр.
        const train = card.querySelector('.fa-train')?.nextElementSibling?.textContent.toLowerCase() || '';
        const wagon = card.querySelector('.fa-box')?.nextElementSibling?.textContent.toLowerCase() || '';
        const code = card.querySelector('.fa-exclamation-triangle')?.nextElementSibling?.textContent.toLowerCase() || '';
        const faultDescription = card.querySelector('.fa-wrench')?.nextElementSibling?.textContent.toLowerCase() || ''; // Поле Описание неисправности
        const fullPath = card.querySelector('.fa-wrench')?.nextElementSibling?.title.toLowerCase() || ''; // Полный путь из title

        // Собираем весь текст, по которому будем искать
        const searchableText = `${fio} ${tabel} ${city} ${train} ${wagon} ${code} ${faultDescription} ${fullPath}`;

        const status = card.dataset.status;

        const matchesSearch = searchText === '' || searchableText.includes(searchText);
        const matchesFilter = filter === 'all' || status === filter;

        card.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
    });
}

// !!! Добавляем обработчики событий только после загрузки DOM !!!
// searchInput.addEventListener('input', filterTasks);
// filterSelect.addEventListener('change', filterTasks);


// --- Код для эффектов hover и нажатия кнопок ---
// !!! Применяем обработчики только к УЖЕ СУЩЕСТВУЮЩИМ кнопкам/карточкам после загрузки DOM !!!
// Для новых карточек, добавленных поллингом, обработчики клика будут работать благодаря делегированию
// Обработчики mouseenter/mouseleave для новых карточек можно добавить после их рендеринга или использовать делегирование для них тоже
/*
 taskListElement.querySelectorAll('.task-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-3px)';
        card.style.boxShadow = '0 8px 20px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04)';
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = '';
        card.style.boxShadow = ''; // Вернуть дефолтный (или задать его в CSS)
    });
});

 taskListElement.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('mousedown', () => btn.style.transform = 'translateY(1px)');
    btn.addEventListener('mouseup', () => btn.style.transform = '');
    btn.addEventListener('mouseleave', () => btn.style.transform = '');
});
*/

// --- Обработка кнопок смены статуса (использует делегирование, работает для новых карточек) ---
// Этот код уже использует делегирование на taskListElement, поэтому он будет работать
// для новых карточек, добавленных поллингом.

// !!! Добавляем этот обработчик после загрузки DOM !!!
/*
 taskListElement.addEventListener('click', async (event) => {
    // ... ваш код обработки клика по кнопкам статуса ...
 });
*/

let latestRequestId = 0; // Начинаем с 0, так как ID > 0

// Функция для получения максимального ID из текущих карточек на странице
function getLatestRequestIdFromCards() {
    const cards = taskListElement.querySelectorAll('.task-card');
    let maxId = 0; // Начинаем с 0

    cards.forEach(card => {
        // В вашем шаблоне у каждой карточки .task-card должен быть атрибут data-request-id="{{ req.id }}"
        const requestId = parseInt(card.dataset.requestId, 10); // Получаем ID и преобразуем в число

        if (!isNaN(requestId) && requestId > maxId) {
            maxId = requestId; // Обновляем, если текущий ID больше
        }
    });
    return maxId; // Возвращает максимальный ID или 0
}

// Переменная для хранения метки времени последней загруженной заявки
// Инициализируется в DOMContentLoaded
let latestRequestTimestamp = null;

// Функция для получения метки времени из ISO строки (для дат, которые nullable)
function parseISODateTime(isoString) {
    if (!isoString) return null;
    try {
        // Важно: Если ваш бэкенд возвращает дату без информации о таймзоне,
        // Luxon может интерпретировать ее как локальное время.
        // Если бэкенд возвращает UTC, используйте { setZone: 'UTC' }
        // Или убедитесь, что бэкенд возвращает дату с таймзоной (например, +00:00 или Z)
        return DateTime.fromISO(isoString, { setZone: 'UTC' }); // Пример с UTC
    } catch (e) {
        console.error("Ошибка парсинга ISO даты:", isoString, e);
        return null;
    }
}

// Функция для получения самой свежей метки времени из текущих карточек на странице
function getLatestTimestampFromCards() {
    const cards = taskListElement.querySelectorAll('.task-card');
    let latestTimestamp = null;

    cards.forEach(card => {
        // В вашем шаблоне у каждой карточки .task-card должен быть атрибут data-created-at="{{ req.created_at.isoformat }}"
        const createdAtISO = card.dataset.createdAt;
        const createdAt = parseISODateTime(createdAtISO);

        if (createdAt && (!latestTimestamp || createdAt > latestTimestamp)) {
            latestTimestamp = createdAt;
        }
    });
    return latestTimestamp; // Возвращает объект Luxon DateTime или null
}


// Функция для отрисовки одной карточки заявки на основе данных из JSON
function renderRequestCard(requestData) {
    const card = document.createElement('div');
    card.classList.add('task-card');
    // Добавляем data-атрибуты из данных заявки (ID, статус, время создания)
    card.dataset.status = requestData.status;
    card.dataset.requestId = requestData.id;
    card.dataset.createdAt = requestData.created_at; // Сохраняем время создания в ISO формате

    card.dataset.classifiedByFio = requestData.classified_by_fio || '';
    card.dataset.classifiedAt = requestData.classified_at || '';

    let cardHTML = `
        <div class="task-header">
            <div class="task-title">Зафиксировал: ${requestData.fio || '-'}</div>
            <div class="task-status status-${requestData.status}">
                ${requestData.status_display || requestData.status || '-'}
            </div>
        </div>
        <div class="task-info">
             <span class="label"><i class="fas fa-hashtag"></i> Табель:</span>
             <span class="value">${requestData.tabel || '-'}</span>
         </div>
        <div class="task-info">
            <span class="label"><i class="far fa-calendar-alt"></i> Дата создания:</span>
            <span class="value">${DateTime.fromISO(requestData.created_at, { setZone: 'UTC' }).toFormat('dd/MM/yyyy HH:mm') || '-'}</span>
        </div>
        `;

         // Информация о городе и дате отправления
         if (requestData.departure_city) {
             cardHTML += `
             <div class="task-info">
                 <span class="label"><i class="fas fa-city"></i> Город отпр.:</span>
                 <span class="value">${requestData.departure_city}</span>
             </div>
             `;
         }
         if (requestData.departure_date) {
              const depDate = parseISODateTime(requestData.departure_date); // Парсим дату отправления
              if (depDate) {
                  cardHTML += `
                  <div class="task-info">
                      <span class="label"><i class="fas fa-calendar-alt"></i> Дата отпр.:</span>
                      <span class="value">${depDate.toFormat('dd/MM/yyyy')}</span>
                  </div>
                  `;
               }
         }

        // Информация о рейсе
        cardHTML += `
        <div class="task-info">
            <span class="label"><i class="fas fa-train"></i> Поезд:</span>
            <span class="value">${requestData.train || '-'}</span>
        </div>
         <div class="task-info">
             <span class="label"><i class="fas fa-box"></i> Вагон:</span>
             <span class="value">${requestData.wagon || '-'}</span>
         </div>
         `;
         // Добавьте route и location если нужны
         if (requestData.route) {
              cardHTML += `
              <div class="task-info">
                  <span class="label"><i class="fas fa-route"></i> Маршрут:</span>
                  <span class="value">${requestData.route}</span>
              </div>
              `;
         }
          if (requestData.location) {
               cardHTML += `
               <div class="task-info">
                   <span class="label"><i class="fas fa-map-marker-alt"></i> Пункт:</span>
                   <span class="value">${requestData.location}</span>
               </div>
               `;
          }

         // Информация о неисправности
         cardHTML += `
          <div class="task-info">
              <span class="label"><i class="fas fa-wrench"></i> Неисправность:</span>
              <span class="value" title="${requestData.path_info || '-'}">
                  ${requestData.fault_description || '-'}
              </span>
          </div>
         <div class="task-info">
             <span class="label"><i class="fas fa-exclamation-triangle"></i> Код:</span>
             <span class="value">${requestData.repair_code || '-'}</span>
         </div>
         `;


        // Блок с таймером или статусом завершения
         if (requestData.status !== 'done' && requestData.deadline) {
              cardHTML += `
              <div class="task-info">
                  <span class="label"><i class="fas fa-clock"></i> Осталось:</span>
                  <span class="value timer" data-deadline="${requestData.deadline}"> 
                      <i class="fas fa-hourglass-half"></i> <span class="time-value">Расчет...</span>
                  </span>
              </div>
              `;
          } else if (requestData.status === 'done') {
               cardHTML += `
                <div class="task-info">
                    <span class="label"><i class="fas fa-check-circle"></i> Статус:</span>
                    <span class="value status-done-text">Ремонт завершен</span>
                </div>
               `;
          }


        // Кнопки действий
         cardHTML += `
         <div class="buttons">
             <button class="btn btn-status-update" data-new-status="done" data-request-id="${requestData.id}" ${requestData.status === 'done' ? 'disabled' : ''}>
                 <i class="fas fa-check"></i> Выполнено
             </button>
             <button class="btn btn-status-update" data-new-status="assigned" data-request-id="${requestData.id}" ${requestData.status === 'assigned' || requestData.status === 'done' ? 'disabled' : ''}>
                 <i class="fas fa-user-tag"></i> В наряд
             </button>
              <button class="btn btn-status-update" data-new-status="urgent" data-request-id="${requestData.id}" ${requestData.status === 'urgent' || requestData.status === 'done' ? 'disabled' : ''}>
                 <i class="fas fa-star"></i> Срочно
             </button>
             <button class="btn btn-delete" data-request-id="${requestData.id}"><i class="fas fa-trash"></i></button>
             <button class="btn btn-more" data-request-id="${requestData.id}"><i class="fas fa-ellipsis-h"></i></button>
         </div>
         `;

    card.innerHTML = cardHTML;

    // Можно добавить эффекты mouseenter/mouseleave для этой новой карточки,
    // если они не реализованы через делегирование событий.
    // Пример для одной карточки:
    // card.addEventListener('mouseenter', () => { card.style.transform = 'translateY(-3px)'; card.style.boxShadow = '0 8px 20px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04)'; });
    // card.addEventListener('mouseleave', () => { card.style.transform = ''; card.style.boxShadow = ''; });


    return card;
}


// Функция для получения новых заявок с подробным логированием (ИСПРАВЛЕНИЯ)
async function fetchNewRequests() {
    const functionCallTime = luxon.DateTime.now();
    console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Вызов fetchNewRequests...`);

    // Получаем максимальный ID из текущих карточек на странице
    const currentLatestId = getLatestRequestIdFromCards(); // ИСПОЛЬЗУЕМ getLatestRequestIdFromCards()
    let url = '/api/requests/latest/';

    if (currentLatestId > 0) { // Отправляем ID только если есть хотя бы одна карточка (ID > 0)
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Найден максимальный ID: <span class="math-inline">\{currentLatestId\}\. Отправка запроса с ?latest\_id\=</span>{currentLatestId}`);
        url += `?latest_id=${currentLatestId}`; // ИСПОЛЬЗУЕМ latest_id параметр
    } else {
         console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Нет карточек на странице (макс ID 0). Отправка запроса без ?latest_id.`);
    }

    try {
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Отправка fetch запроса на: ${url}`);
        const response = await fetch(url);
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Ответ от ${url}: Статус ${response.status}`);

        if (!response.ok) {
            console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Ошибка HTTP! Статус: ${response.status}`);
            try {
                const errorBody = await response.text();
                console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Тело ответа с ошибкой:`, errorBody);
            } catch (e) {
                 console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Не удалось прочитать тело ответа с ошибкой.`);
            }
            return;
        }

        const result = await response.json();
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Получен JSON ответ:`, JSON.stringify(result, null, 2));

        if (result && result.status === 'success' && Array.isArray(result.requests)) {
             console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Ответ корректный. Статус: ${result.status}. Количество новых заявок: ${result.requests.length}`);

             if (result.requests.length > 0) {
                 const taskList = document.getElementById('task-list');
                 if (taskList) {
                     console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Найден #task-list. Начинаю добавление ${result.requests.length} карточек...`);
                     // Добавляем в обратном порядке, чтобы новые были сверху, но в порядке их создания
                     result.requests.reverse().forEach(requestData => {
                         console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Рендеринг карточки для ID: ${requestData.id}`, requestData);

                         if (taskList.querySelector(`.task-card[data-request-id="${requestData.id}"]`)) {
                            console.warn(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Карточка с ID ${requestData.id} уже существует на странице. Пропускаю добавление дубликата.`);
                            return;

                        }

                         const newCard = renderRequestCard(requestData);
                         if (newCard instanceof HTMLElement) {
                             taskList.prepend(newCard); // Добавляем в начало списка
                             console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Карточка для ID ${requestData.id} добавлена в DOM.`);
                         } else {
                             console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Функция renderRequestCard НЕ вернула HTML элемент для ID: ${requestData.id}`, newCard);
                         }
                     });
                     console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Добавление карточек завершено. Вызов updateTimers и filterTasks...`);

                     // После добавления новых карточек, нужно обновить таймеры и фильтрацию
                     updateTimers();
                     filterTasks();

                     // !!! ИСПРАВЛЕНО: Обновляем latestRequestId после успешного добавления новых карточек !!!
                     latestRequestId = getLatestRequestIdFromCards();
                     console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] latestRequestId обновлен до: ${latestRequestId}`);


                 } else {
                      console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] ОШИБКА: Элемент #task-list НЕ НАЙДЕН в DOM!`);
                 }
             } else {
                  // console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Новых заявок для отображения нет.`);
             }

        } else {
             console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] Структура ответа API некорректна. Ожидался status='success' и массив 'requests'. Получено:`, result);
        }

    } catch (error) {
        console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] КРИТИЧЕСКАЯ ОШИБКА в fetchNewRequests:`, error);
    }
}

// --- Инициализация при загрузке DOM ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM полностью загружен. Инициализация диспетчерской панели.");

    // Инициализируем latestRequestTimestamp при загрузке страницы на основе уже загруженных данных
    // Убедитесь, что в вашем Django шаблоне у каждой карточки .task-card есть атрибут data-created-at="{{ req.created_at.isoformat }}"
    latestRequestTimestamp = getLatestTimestampFromCards();
    console.log("Изначальный максимальный ID заявки:", latestRequestId);

    // Запускаем периодический опрос сервера
    const pollingInterval = 15000; // Интервал опроса в миллисекундах (15 секунд)
    setInterval(fetchNewRequests, pollingInterval);

    // Применяем обработчики событий фильтрации и поиска
    if(searchInput && filterSelect) {
        searchInput.addEventListener('input', filterTasks);
        filterSelect.addEventListener('change', filterTasks);
        filterTasks(); // Вызываем фильтрацию один раз при загрузке на случай, если есть фильтр в URL или нужно применить начальный
    } else {
        console.error("Элементы поиска или фильтра не найдены!");
    }


    // Применяем обработчики событий клика кнопок через делегирование
    if (taskListElement) {
    taskListElement.addEventListener('click', async (event) => {
        const deleteButton = event.target.closest('.btn-delete');
        const statusButton = event.target.closest('.btn-status-update');

        // --- Логика для кнопки УДАЛЕНИЯ ---
        if (deleteButton) {
            if (!confirm("Вы уверены, что хотите удалить эту заявку?")) {
                return;
            }

            const card = deleteButton.closest('.task-card');
            const requestId = card.dataset.requestId;

            if (!requestId || requestId === 'unknown') {
                console.warn("Не удалось получить ID заявки для удаления.");
                alert("Ошибка: Не удалось определить ID заявки для удаления.");
                return;
            }

            const url = `/api/request/${requestId}/delete/`;
            const csrftoken = getCookie('csrftoken');

            if (!csrftoken) {
                alert("Ошибка безопасности (CSRF). Попробуйте обновить страницу.");
                return;
            }

            try {
                deleteButton.disabled = true;
                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrftoken,
                    },
                });

                if (response.headers.get('content-type')?.includes('application/json')) {
                    const result = await response.json();

                    if (response.ok && result.status === 'success') {
                        console.log(`Заявка ${requestId} успешно удалена.`);
                        card.remove();
                    } else {
                        alert(`Ошибка удаления заявки: ${result.message || response.statusText || 'Неизвестная ошибка сервера.'}`);
                        console.error(`Ошибка API при удалении заявки ${requestId}:`, response.status, result);
                        deleteButton.disabled = false;
                    }
                } else {
                    const errorText = await response.text();
                    alert(`Ошибка сервера при удалении заявки ${requestId}: ${response.status} ${response.statusText}`);
                    console.error(`Сервер вернул не-JSON ответ при удалении заявки ${requestId}:`, response.status, response.statusText, errorText);
                    deleteButton.disabled = false;
                }

            } catch (error) {
                console.error(`Сетевая ошибка при удалении заявки ${requestId}:`, error);
                alert('Произошла сетевая ошибка при удалении заявки. Проверьте соединение.');
                deleteButton.disabled = false;
            }
        }

        // --- Логика для кнопки СМЕНЫ СТАТУСА ---
        if (statusButton) {
            const card = statusButton.closest('.task-card');
            const requestId = card.dataset.requestId;
            const newStatus = statusButton.dataset.newStatus;

            if (!requestId || !newStatus) {
                console.warn("Не удалось получить ID заявки или новый статус из data-атрибутов кнопки.");
                alert("Ошибка: Не удалось определить ID заявки или новый статус.");
                return;
            }

            const url = `/api/request/${requestId}/update_status/`;
            const csrftoken = getCookie('csrftoken');
            if (!csrftoken) {
                alert("Ошибка безопасности (CSRF). Попробуйте обновить страницу.");
                return;
            }

            try {
                statusButton.disabled = true;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    console.log(`Статус заявки ${requestId} успешно обновлен на ${newStatus}.`);

                    card.dataset.status = newStatus;

                    const statusTextMap = {
                        'pending': 'В ожидании',
                        'assigned': 'В наряде',
                        'in_progress': 'В работе',
                        'classified': 'Классифицирована',
                        'completed': 'Выполнена',
                        'cancelled': 'Отменена',
                    };
                    const statusElement = card.querySelector('.task-status');
                    if (statusElement) {
                        statusElement.textContent = statusTextMap[newStatus] || newStatus;
                        statusElement.className = `task-status status-${newStatus}`;
                    }

                    // --- Логика пере-блокировки/разблокировки кнопок ---
                    card.querySelectorAll('.btn-status-update').forEach(btn => {
                        const btnTargetStatus = btn.dataset.newStatus;

                        btn.disabled = false; // По умолчанию разблокируем

                        // Блокируем кнопку, если ее целевой статус совпадает с новым
                        if (btnTargetStatus === newStatus) {
                            btn.disabled = true;
                        }

                        // Дополнительная логика блокировки в зависимости от нового статуса
                        if (newStatus === 'completed' || newStatus === 'cancelled') {
                            btn.disabled = true; // Блокируем все при завершении/отмене
                        } else if (newStatus === 'assigned') {
                            if (btnTargetStatus === 'pending') {
                                btn.disabled = true; // Из assigned нельзя перевести в pending
                            }
                        } else if (newStatus === 'in_progress') {
                            if (btnTargetStatus === 'pending' || btnTargetStatus === 'assigned') {
                                btn.disabled = true; // Из in_progress нельзя в pending/assigned
                            }
                        } else if (newStatus === 'classified') {
                            if (btnTargetStatus === 'pending') {
                                btn.disabled = true; // Из classified нельзя в pending
                            }
                        }
                        // Добавьте логику для других статусов, если нужно (e.g., из pending нельзя в assigned без классификации?)
                        // Текущая логика позволит из pending перейти в assigned, classified, urgent
                        // Из assigned можно в in_progress, completed, cancelled, urgent
                        // Из classified можно в assigned, in_progress, completed, cancelled, urgent
                    });
                    // --- Конец логики пере-блокировки ---


                    // Если статус 'completed', убираем таймер или меняем его текст
                    const timerElement = card.querySelector('.timer');
                    if (newStatus === 'completed' && timerElement) {
                        timerElement.closest('.task-info').innerHTML = `<span class="label"><i class="fas fa-check-circle"></i> Статус:</span><span class="value status-completed-text">Выполнена</span>`;
                    } else if (newStatus !== 'completed' && !card.querySelector('.timer') && card.dataset.deadline) {
                         // Логика восстановления таймера, если статус вернулся с завершенного, сложна и требует доп. данных
                         // Сейчас просто игнорируем этот случай или предлагаем обновить страницу.
                     }

                } else {
                    alert(`Ошибка обновления статуса: ${result.message || response.statusText || 'Неизвестная ошибка'}`);
                    console.error(`Ошибка API при обновлении статуса ${requestId} на ${newStatus}:`, response.status, result);
                    statusButton.disabled = false; // Используем statusButton
                }

            } catch (error) {
                console.error(`Сетевая ошибка при обновлении статуса ${requestId} на ${newStatus}:`, error);
                alert('Произошла сетевая ошибка при обновлении статуса. Проверьте соединение.');
                statusButton.disabled = false; // Используем statusButton
            }
        }

         // --- Логика для кнопки "Подробнее" (если есть) ---
         const moreButton = event.target.closest('.btn-more');
         if (moreButton) {
              const card = moreButton.closest('.task-card');
              const requestId = card.dataset.requestId;
              console.log(`Нажата кнопка "Подробнее" для заявки ID: ${requestId}`);
              alert(`Функция "Подробнее" для заявки ${requestId} пока не реализована.`);
              // Здесь может быть вызов openDetailsModal(requestId);
         }


    });
} else {
    console.error("Элемент #task-list не найден в DOM.");
}


    // Запускаем обновление таймеров для всех карточек (включая изначально загруженные)
     // Делаем это после того, как DOM полностью загружен и карточки присутствуют
     updateTimers();
     // Запускаем периодическое обновление таймеров
     setInterval(updateTimers, 30000); // Обновляем каждые 30 секунд

});