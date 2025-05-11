const allData = {
    "ПЭМ": {
        "Электрооборудование": {
             "Освещение": {"Не горит лампа": "E001", "Мерцает свет": "E002"},
             "Розетки": {"Нет напряжения": "E003", "Повреждена": "E004"}
        },
        "Климат-контроль": {
             "Не греет": {"Слабый нагрев": "C001", "Нет нагрева": "C002"},
             "Не охлаждает": {"Слабое охлаждение": "C003", "Нет охлаждения": "C004"}
        }
        }, // Оставляем пустыми, как в оригинале
    "ПДК": {},
    "Ревизор": {}
};


const { DateTime, Duration } = luxon;

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

const updateTimers = () => {
    document.querySelectorAll('.timer').forEach(timer => {
        if (!timer.dataset.deadline) return;
        const deadline = DateTime.fromISO(timer.dataset.deadline);
        const now = DateTime.now();
        const timeValueSpan = timer.querySelector('.time-value');
        if (!timeValueSpan) return;

        if (deadline <= now) {
            timeValueSpan.textContent = 'Просрочено';
            timer.classList.remove('normal', 'warning');
            timer.classList.add('urgent');
            return;
        }

        const diff = deadline.diff(now, ['days', 'hours', 'minutes', 'seconds']).toObject();
        let timeString = '';
         if (diff.days > 0) timeString += `${Math.floor(diff.days)}д `;
        if (diff.hours > 0 || diff.days > 0) timeString += `${Math.floor(diff.hours)}ч `;
         if (diff.minutes > 0 || diff.hours > 0 || diff.days > 0 || timeString === '') timeString += `${Math.floor(diff.minutes)}м`;
        timeValueSpan.textContent = timeString.trim();

        const totalMinutes = (diff.days * 24 * 60) + (diff.hours * 60) + diff.minutes;
        timer.classList.remove('normal', 'warning', 'urgent');
        if (totalMinutes < 60) timer.classList.add('urgent');
        else if (totalMinutes < (6 * 60)) timer.classList.add('warning');
        else timer.classList.add('normal');
    });
};

const searchInput = document.getElementById('search');
const filterSelect = document.getElementById('filter');
const taskListElement = document.getElementById('task-list');

function filterTasks() {
    if (!taskListElement) return;
    const searchText = searchInput ? searchInput.value.toLowerCase() : '';
    const filter = filterSelect ? filterSelect.value : 'all';

    taskListElement.querySelectorAll('.task-card').forEach(card => {
        const train = card.querySelector('.fa-train')?.nextElementSibling?.textContent.toLowerCase() || '';
        const wagon = card.querySelector('.fa-box')?.nextElementSibling?.textContent.toLowerCase() || '';
        const city = card.querySelector('.fa-city')?.nextElementSibling?.textContent.toLowerCase() || '';
        const searchableText = `${train} ${wagon} ${city}`; // Поиск для ПЭМ в основном по поезду/вагону/городу
        const status = card.dataset.status;
        const matchesSearch = searchText === '' || searchableText.includes(searchText);
        const matchesFilter = filter === 'all' || status === filter;
        card.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
    });
}

let latestRequestId = 0;

function getLatestRequestIdFromCards() {
    if (!taskListElement) return 0;
    const cards = taskListElement.querySelectorAll('.task-card');
    let maxId = 0;
    cards.forEach(card => {
        const requestId = parseInt(card.dataset.requestId, 10);
        if (!isNaN(requestId) && requestId > maxId) {
            maxId = requestId;
        }
    });
    return maxId;
}

function parseISODateTime(isoString) {
    if (!isoString) return null;
    try {
        return DateTime.fromISO(isoString, { setZone: 'UTC' });
    } catch (e) {
        console.error("Ошибка парсинга ISO даты:", isoString, e);
        return null;
    }
}

function renderRequestCard(requestData) {
    const card = document.createElement('div');
    card.classList.add('task-card');
    card.classList.add('clickable'); // Добавляем класс для индикации кликабельности
    card.dataset.status = requestData.status || 'unknown';
    card.dataset.requestId = requestData.id || 'unknown';
    card.dataset.createdAt = requestData.created_at || '';
    // Сохраняем путь и код, если они есть, для модального окна
    card.dataset.pathInfo = requestData.path_info || '[]';
    card.dataset.repairCode = requestData.repair_code || '';

    let departureCityHTML = '';
    if (requestData.departure_city) {
        departureCityHTML = `
        <div class="task-info">
            <span class="label"><i class="fas fa-city"></i> Город отпр.:</span>
            <span class="value">${requestData.departure_city}</span>
        </div>`;
    }

    let departureDateHTML = '';
    if (requestData.departure_date) {
         const depDate = parseISODateTime(requestData.departure_date);
         if (depDate) {
             departureDateHTML = `
             <div class="task-info">
                 <span class="label"><i class="fas fa-calendar-alt"></i> Дата отпр.:</span>
                 <span class="value">${depDate.toFormat('dd/MM/yyyy')}</span>
             </div>`;
          }
    }

    let timerHTML = '';
     // Для ПЭМ таймер может быть не так важен, как сам факт наличия заявки
     // Оставляем его, если deadline передается API
    if (requestData.status !== 'done' && requestData.status !== 'classified' && requestData.deadline) {
        timerHTML = `
        <div class="task-info">
            <span class="label"><i class="fas fa-clock"></i> Дедлайн:</span>
            <span class="value timer" data-deadline="${requestData.deadline}"> 
                <i class="fas fa-hourglass-half"></i> <span class="time-value">Расчет...</span>
            </span>
        </div>`;
    } else if (requestData.status === 'done') {
         timerHTML = `
          <div class="task-info">
              <span class="label"><i class="fas fa-check-circle"></i> Статус:</span>
              <span class="value status-done-text">Ремонт завершен</span>
          </div>`;
    } else if (requestData.status === 'classified') {
        timerHTML = `
         <div class="task-info">
             <span class="label"><i class="fas fa-check-double"></i> Статус:</span>
             <span class="value status-classified-text">Классифицировано</span>
         </div>`;
   }

    // Основная информация
    card.innerHTML = `
        <div class="task-header">
            <div class="task-title">Поезд: ${requestData.train || '-'} / Вагон: ${requestData.wagon || '-'}</div>
            <div class="task-status status-${requestData.status || 'unknown'}">
                ${requestData.status_display || requestData.status || '-'}
            </div>
        </div>
        <div class="task-info">
             <span class="label"><i class="fas fa-user"></i> Заявил:</span>
             <span class="value">${requestData.fio || '-'} (${requestData.role || '?'})</span>
         </div>
         <div class="task-info">
            <span class="label"><i class="far fa-calendar-alt"></i> Дата создания:</span>
            <span class="value">${requestData.created_at ? DateTime.fromISO(requestData.created_at, { setZone: 'UTC' }).toFormat('dd/MM/yyyy HH:mm') : '-'}</span>
        </div>
        ${departureCityHTML}
        ${departureDateHTML}
        <div class="task-info">
             <span class="label"><i class="fas fa-wrench"></i> Первичная неиспр.:</span>
             <span class="value" title="${requestData.path_info || '-'}">
                 ${requestData.fault_description || '-'}
             </span>
         </div>
        <div class="task-info">
            <span class="label"><i class="fas fa-exclamation-triangle"></i> Первичный код:</span>
            <span class="value">${requestData.repair_code || 'Нет'}</span>
        </div>
        ${timerHTML}
        <div class="pem-click-hint">Кликните для классификации</div> 
    `;
    // Убрали кнопки изменения статуса, так как основное действие - классификация
    return card;
}

async function fetchNewRequests() {
    const functionCallTime = luxon.DateTime.now();
    console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Вызов fetchNewRequests...`);

    const currentLatestId = getLatestRequestIdFromCards();
    let url = '/api/requests/pem/'; // <<< URL API для ПЭМ

    if (currentLatestId > 0) {
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Найден макс ID: ${currentLatestId}. Запрос с ?latest_id=${currentLatestId}`);
        url += `?latest_id=${currentLatestId}`;
    } else {
         console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Нет карточек (макс ID 0). Запрос без ?latest_id.`);
    }

    try {
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Отправка fetch на: ${url}`);
        const response = await fetch(url);
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Ответ от ${url}: Статус ${response.status}`);

        if (!response.ok) {
            console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Ошибка HTTP! Статус: ${response.status}`);
            // ... (обработка текста ошибки) ...
            return;
        }

        const result = await response.json();
        console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Получен JSON:`, JSON.stringify(result, null, 2));

        if (result && result.status === 'success' && Array.isArray(result.requests)) {
             console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Ответ корректный. Новых заявок: ${result.requests.length}`);

             if (result.requests.length > 0) {
                 const taskList = document.getElementById('task-list');
                 if (taskList) {
                     console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Найден #task-list. Добавление ${result.requests.length} карточек...`);
                     result.requests.reverse().forEach(requestData => {
                         console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Рендеринг ID: ${requestData.id}`);

                         if (taskList.querySelector(`.task-card[data-request-id="${requestData.id}"]`)) {
                            console.warn(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Карточка ID ${requestData.id} уже есть. Пропуск дубликата.`);
                            return;
                         }

                         const newCard = renderRequestCard(requestData);
                         if (newCard instanceof HTMLElement) {
                             taskList.prepend(newCard);
                             console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Карточка ID ${requestData.id} добавлена.`);
                         } else {
                             console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: renderRequestCard НЕ вернула HTML элемент для ID: ${requestData.id}`);
                         }
                     });
                     console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Добавление завершено. Вызов updateTimers и filterTasks...`);
                     updateTimers();
                     filterTasks();
                     latestRequestId = getLatestRequestIdFromCards(); // Обновляем ID после добавления
                     console.log(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: latestRequestId обновлен до: ${latestRequestId}`);
                 } else {
                      console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: ОШИБКА: #task-list НЕ НАЙДЕН!`);
                 }
             }

        } else {
             console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: Структура ответа API некорректна.`, result);
        }

    } catch (error) {
        console.error(`[${functionCallTime.toFormat('HH:mm:ss.SSS')}] PEM: КРИТИЧЕСКАЯ ОШИБКА в fetchNewRequests:`, error);
    }
}


// --- Логика Модального Окна Классификации ---

// Предполагаем, что структура allData загружена глобально или доступна иначе
// const allData = { "ПЭМ": { /* структура неисправностей ПЭМ */ } }; // Должна быть определена!

let modalCurrentRequestId = null;
let modalCurrentPath = [];
let modalSelectedCode = null;
const modalElement = document.getElementById('classification-modal');
const modalBreadcrumbDiv = document.getElementById('modal-breadcrumb');
const modalButtonsDiv = document.getElementById('modal-buttons');
const modalMainTitle = document.getElementById('modal-main-title');
const modalFinalCodeDiv = document.getElementById('modal-final-code');
const modalSelectedCodeSpan = document.getElementById('modal-selected-code');
const modalSubmitButton = document.getElementById('modal-submit-button');
const modalRequestDetailsDiv = document.getElementById('modal-request-details');

function openClassificationModal(requestId, cardElement) {
    if (!allData || !allData['ПЭМ']) {
         console.error("Данные для классификации ПЭМ (allData['ПЭМ']) не найдены!");
         alert("Ошибка: Невозможно открыть окно классификации - отсутствуют данные о неисправностях.");
         return;
     }
    if (!modalElement || !modalSubmitButton || !modalFinalCodeDiv || !modalSelectedCodeSpan || !modalMainTitle || !modalButtonsDiv || !modalBreadcrumbDiv || !modalRequestDetailsDiv) {
         console.error("Один или несколько элементов модального окна не найдены в DOM!");
         alert("Ошибка интерфейса: Не удалось инициализировать окно классификации.");
         return;
     }

    modalCurrentRequestId = requestId;
    modalCurrentPath = [];
    modalSelectedCode = null;
    modalSubmitButton.disabled = true;
    modalFinalCodeDiv.style.display = 'none';

    document.getElementById('modal-request-id').textContent = `(#${requestId})`;

    const train = cardElement.querySelector('.fa-train')?.nextElementSibling?.textContent || '?';
    const wagon = cardElement.querySelector('.fa-box')?.nextElementSibling?.textContent || '?';
    const initialDesc = cardElement.querySelector('.fa-wrench span.value')?.textContent.trim() || 'Нет'; // Используем span.value
    const initialCode = cardElement.querySelector('.fa-exclamation-triangle span.value')?.textContent.trim() || 'Нет';
    modalRequestDetailsDiv.innerHTML = `
        Поезд: ${train}, Вагон: ${wagon}<br>
        Первичное описание: ${initialDesc}<br>
        Первичный код: ${initialCode}
    `;

    renderModalButtons(allData['ПЭМ']);
    modalElement.style.display = 'block';
}

function closeClassificationModal() {
    if(modalElement) modalElement.style.display = 'none';
    modalCurrentRequestId = null;
}

function renderModalButtons(currentData) {
     if (!modalButtonsDiv || !modalMainTitle || !modalFinalCodeDiv || !modalSubmitButton) return;
     updateModalBreadcrumb();
     modalButtonsDiv.innerHTML = "";
     modalFinalCodeDiv.style.display = 'none';
     modalSubmitButton.disabled = true;

     if (modalCurrentPath.length > 0) {
         const backButton = document.createElement("button");
         backButton.textContent = "Назад";
         backButton.classList.add("back-btn");
         backButton.onclick = () => {
             modalCurrentPath.pop();
             renderModalButtons(getModalCurrentData());
         };
         modalButtonsDiv.appendChild(backButton);
     }

     if (typeof currentData === "string") {
         modalSelectedCode = currentData;
         modalSelectedCodeSpan.textContent = modalSelectedCode;
         modalFinalCodeDiv.style.display = 'block';
         modalSubmitButton.disabled = false;
         modalMainTitle.textContent = "Код неисправности выбран";
     } else if (typeof currentData === 'object' && currentData !== null) {
          modalMainTitle.textContent = modalCurrentPath.length === 0 ? "Выберите категорию (ПЭМ)" : "Выберите подкатегорию (ПЭМ)";
          const keys = Object.keys(currentData);
          if (keys.length === 0) {
               modalButtonsDiv.textContent = "В этой категории нет данных.";
          } else {
               keys.forEach(key => {
                    const button = document.createElement("button");
                    button.textContent = key;
                    button.onclick = () => {
                         modalCurrentPath.push(key);
                         renderModalButtons(getModalCurrentData());
                    };
                    modalButtonsDiv.appendChild(button);
               });
          }
     } else {
          modalButtonsDiv.textContent = "Нет данных для отображения.";
     }
}

function getModalCurrentData() {
    let data = allData['ПЭМ'];
    if (!data) return {};
    try {
         modalCurrentPath.forEach(key => {
             if (data && typeof data === 'object') { // Добавим проверку
                 data = data[key];
             } else {
                  throw new Error("Неверный путь или структура данных"); // Выбросим ошибку если что-то не так
             }
         });
         return data || {};
    } catch (e) {
        console.error("Ошибка при получении данных для модального окна:", e, "Путь:", modalCurrentPath);
        modalButtonsDiv.textContent = "Ошибка загрузки данных для этой категории."; // Сообщим об ошибке
        return null; // Вернем null чтобы прервать рендеринг кнопок дальше
    }
}

function updateModalBreadcrumb() {
     if (!modalBreadcrumbDiv) return;
     modalBreadcrumbDiv.innerHTML = "";
     if (modalCurrentPath.length === 0) return;

     const homeLink = document.createElement("a");
     homeLink.href = "#";
     homeLink.textContent = "ПЭМ";
     homeLink.onclick = (e) => { e.preventDefault(); modalCurrentPath = []; renderModalButtons(allData['ПЭМ']); };
     modalBreadcrumbDiv.appendChild(homeLink);

     let currentDataForBreadcrumb = allData['ПЭМ'];
     modalCurrentPath.forEach((level, index) => {
          if (!currentDataForBreadcrumb || typeof currentDataForBreadcrumb !== 'object') return; // Предохранитель

         const separator = document.createElement("span");
         separator.textContent = " › ";
         modalBreadcrumbDiv.appendChild(separator);
         if (index < modalCurrentPath.length - 1) {
              const levelLink = document.createElement("a");
              levelLink.href = "#";
              levelLink.textContent = level;
              levelLink.onclick = ((levelIndex) => (e) => {
                   e.preventDefault();
                   modalCurrentPath = modalCurrentPath.slice(0, levelIndex + 1);
                   renderModalButtons(getModalCurrentData());
              })(index);
               modalBreadcrumbDiv.appendChild(levelLink);
         } else {
             const levelText = document.createElement("span");
             levelText.textContent = level;
             modalBreadcrumbDiv.appendChild(levelText);
         }
         currentDataForBreadcrumb = currentDataForBreadcrumb[level];
     });
 }

async function submitClassification() {
     if (!modalCurrentRequestId || !modalSelectedCode || !Array.isArray(modalCurrentPath) || modalCurrentPath.length === 0) {
         alert("Ошибка: Не выбрана полная классификация или не определена заявка.");
         return;
     }

     const url = `/api/request/${modalCurrentRequestId}/classify/`;
     const dataToSend = {
         path: modalCurrentPath,
         code: modalSelectedCode
     };
     const csrftoken = getCookie('csrftoken');
     if (!csrftoken) {
          alert("Ошибка безопасности (CSRF). Попробуйте обновить страницу.");
          return;
     }

     console.log(`Отправка классификации для ID ${modalCurrentRequestId}:`, dataToSend);
     if(modalSubmitButton) modalSubmitButton.disabled = true;

     try {
         const response = await fetch(url, {
             method: 'POST',
             headers: {
                 'Content-Type': 'application/json',
                 'X-CSRFToken': csrftoken
             },
             body: JSON.stringify(dataToSend)
         });

         const result = await response.json();

         if (response.ok && result.status === 'success') {
             alert(result.message || `Заявка #${modalCurrentRequestId} успешно классифицирована.`);
             closeClassificationModal();

             const cardToRemove = taskListElement.querySelector(`.task-card[data-request-id="${modalCurrentRequestId}"]`);
             if (cardToRemove) {
                  console.log(`Удаление карточки ID ${modalCurrentRequestId} с панели ПЭМ.`);
                  cardToRemove.remove();
             }
             // Возможно, стоит обновить счетчики (если они есть на панели ПЭМ)
         } else {
             alert(`Ошибка классификации: ${result.message || 'Неизвестная ошибка сервера.'}`);
             if(modalSubmitButton) modalSubmitButton.disabled = false;
         }
     } catch (error) {
         console.error("Сетевая ошибка при отправке классификации:", error);
         alert("Произошла сетевая ошибка при отправке классификации.");
         if(modalSubmitButton) modalSubmitButton.disabled = false;
     }
}

// --- Инициализация при загрузке DOM ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM полностью загружен. Инициализация панели ПЭМ.");

    // Инициализируем latestRequestId при загрузке страницы
    latestRequestId = getLatestRequestIdFromCards(); // Правильная инициализация
    console.log("Изначальный максимальный ID заявки на панели ПЭМ:", latestRequestId);

    const pollingInterval = 15000;
    setInterval(fetchNewRequests, pollingInterval);
    console.log(`Поллинг API ПЭМ запущен с интервалом ${pollingInterval / 1000} сек.`);

    if(searchInput) searchInput.addEventListener('input', filterTasks);
    if(filterSelect) filterSelect.addEventListener('change', filterTasks);
    filterTasks();

    if(taskListElement) {
        // Делегированный обработчик клика для КАРТОЧЕК (открытие модалки)
         taskListElement.addEventListener('click', (event) => {
             const card = event.target.closest('.task-card.clickable'); // Ищем кликабельную карточку
             const buttonClicked = event.target.closest('.btn'); // Проверяем клик по кнопке

             if (card && !buttonClicked) {
                  const requestId = card.dataset.requestId;
                  if (requestId && requestId !== 'unknown') {
                       console.log("Клик по карточке ID:", requestId, "для классификации.");
                       openClassificationModal(requestId, card);
                  } else {
                       console.warn("Не удалось получить ID заявки из карточки.");
                  }
             }
         });

        // Делегированный обработчик клика для КНОПОК СТАТУСА (если они нужны ПЭМ)
        taskListElement.addEventListener('click', async (event) => {
            const button = event.target.closest('.btn-status-update');
            if (!button) return;

            const card = button.closest('.task-card');
            const requestId = card?.dataset.requestId;
            const newStatus = button.dataset.newStatus;

            if (!requestId || !newStatus) {
                 console.warn("Не удалось получить ID заявки или новый статус из data-атрибутов кнопки.");
                 return;
            }
             if (requestId === 'unknown') return; // Не обрабатывать кнопки на ошибочных карточках

            const url = `/api/request/${requestId}/update_status/`;
            const csrftoken = getCookie('csrftoken');
             if (!csrftoken) { alert("Ошибка CSRF."); return; }

            try {
                 button.disabled = true;
                 const response = await fetch(url, { /* ... POST запрос для смены статуса ... */ });
                 const result = await response.json();

                 if (response.ok && result.status === 'success') {
                     console.log(`Статус заявки ${requestId} обновлен на ${newStatus}.`);
                     card.dataset.status = newStatus;
                     const statusElement = card.querySelector('.task-status');
                     const statusTextMap = { /* ... ваши статусы ... */ };
                     if(statusElement) {
                         statusElement.textContent = statusTextMap[newStatus] || newStatus;
                         statusElement.className = `task-status status-${newStatus}`;
                     }
                     // ... (логика блокировки/разблокировки кнопок) ...
                     // ... (обновление таймера/статуса) ...
                 } else {
                     alert(`Ошибка обновления статуса: ${result.message || 'Неизвестная ошибка'}`);
                     button.disabled = false;
                 }
            } catch (error) {
                console.error('Ошибка сети при обновлении статуса:', error);
                alert('Произошла ошибка при обновлении статуса.');
                button.disabled = false;
            }
        });

    } else {
        console.error("Элемент #task-list не найден!");
    }

    updateTimers();
    setInterval(updateTimers, 30000);
    console.log("Инициализация панели ПЭМ завершена.");
});