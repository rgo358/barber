// 📱 TELEGRAM WEB APP BOOKING LOGIC

// === ИНИЦИАЛИЗАЦИЯ ===
let tg = window.Telegram.WebApp;
let state = {
    step: 'service',
    selectedService: null,
    selectedMaster: null,
    selectedDate: null,
    selectedTime: null,
    services: {},
    masters: {},
    prices: {}
};

// === КОНФИГУРАЦИЯ САЛОНА (из salon_bot.py) ===
const CONFIG = {
    services: {
        'Женская стрижка': 0,
        'Мужская стрижка': 0,
        'Детская стрижка': 0,
        'Стрижка бороды': 0,
        'Сложное окрашивание': 0,
        'Свадебные и вечерние причёски': 0
    },
    masters: ['Дмитрий', 'Александр', 'Игорь'],
    workingHours: {
        start: '08:00',
        end: '18:00',
        lunch: '12:00-13:00'
    }
};

// === ИНИЦИАЛИЗАЦИЯ TELEGRAM WEB APP ===
function initTelegram() {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#1a1a1a');
    tg.setBackgroundColor('#1a1a1a');
    console.log('✅ Telegram Web App инициализирована');
    console.log('User ID:', tg.initDataUnsafe.user?.id);
}

// === ЗАГРУЗКА ДАННЫХ ===
async function loadData() {
    try {
        // Загружаем доступные времена с API
        const response = await fetch('/api/available-times', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date: new Date().toISOString().split('T')[0] })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Данные загружены:', data);
        }
    } catch (error) {
        console.log('⚠️  API недоступен (используем локальные данные):', error);
    }
    
    initUI();
}

// === ИНИЦИАЛИЗАЦИЯ UI ===
function initUI() {
    renderServices();
    attachEventListeners();
}

// === РЕНДЕР УСЛУГ ===
function renderServices() {
    const container = document.getElementById('services-container');
    container.innerHTML = '';
    
    Object.entries(CONFIG.services).forEach(([service, price]) => {
        const btn = document.createElement('button');
        btn.className = 'service-btn';
        btn.innerHTML = `
            <div>✂️ ${service}</div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">
                ${price > 0 ? price + '₽' : 'по запросу'}
            </div>
        `;
        btn.addEventListener('click', () => selectService(service));
        container.appendChild(btn);
    });
}

// === ВЫБОР УСЛУГИ ===
function selectService(service) {
    state.selectedService = service;
    state.step = 'master';
    
    console.log('✅ Выбрана услуга:', service);
    showStep('master');
    renderMasters();
    highlightActive('service', service);
}

// === РЕНДЕР МАСТЕРОВ ===
function renderMasters() {
    const container = document.getElementById('masters-container');
    container.innerHTML = '';
    
    CONFIG.masters.forEach(master => {
        const btn = document.createElement('button');
        btn.className = 'master-btn';
        btn.innerHTML = `
            <div>👨‍💼 ${master}</div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">⭐ 5.0</div>
        `;
        btn.addEventListener('click', () => selectMaster(master));
        container.appendChild(btn);
    });
}

// === ВЫБОР МАСТЕРА ===
function selectMaster(master) {
    state.selectedMaster = master;
    state.step = 'date';
    
    console.log('✅ Выбран мастер:', master);
    showStep('date');
    renderCalendar();
    highlightActive('master', master);
}

// === РЕНДЕР КАЛЕНДАРЯ ===
function renderCalendar() {
    const container = document.getElementById('calendar-container');
    container.innerHTML = '';
    
    const today = new Date();
    const month = today.getMonth();
    const year = today.getFullYear();
    
    const header = document.createElement('div');
    header.className = 'calendar-header';
    header.innerHTML = `
        <button class="calendar-nav-prev">◀️</button>
        <h3>${getMonthName(month)} ${year}</h3>
        <button class="calendar-nav-next">▶️</button>
    `;
    container.appendChild(header);
    
    const days = document.createElement('div');
    days.className = 'calendar-days';
    
    // Дни недели
    ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].forEach(day => {
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day-header';
        dayEl.textContent = day;
        days.appendChild(dayEl);
    });
    
    // Даты месяца
    const firstDay = new Date(year, month, 1).getDay();
    const lastDay = new Date(year, month + 1, 0).getDate();
    
    // Пустые клетки в начале
    for (let i = 1; i < firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'calendar-day disabled';
        days.appendChild(empty);
    }
    
    // Даты
    for (let date = 1; date <= lastDay; date++) {
        const dateEl = document.createElement('button');
        dateEl.className = 'calendar-day';
        dateEl.textContent = date;
        
        const d = new Date(year, month, date);
        const dateStr = d.toISOString().split('T')[0];
        
        // Проверки
        if (d < today && d.toDateString() !== today.toDateString()) {
            dateEl.classList.add('disabled');
            dateEl.disabled = true;
        } else if (d.toDateString() === today.toDateString()) {
            dateEl.classList.add('today');
        }
        
        if (d >= today) {
            dateEl.addEventListener('click', () => selectDate(dateStr));
        }
        
        days.appendChild(dateEl);
    }
    
    container.appendChild(days);
}

// === ВЫБОР ДАТЫ ===
function selectDate(date) {
    state.selectedDate = date;
    state.step = 'time';
    
    console.log('✅ Выбрана дата:', date);
    showStep('time');
    renderTimes();
}

// === РЕНДЕР ВРЕМЕНИ ===
function renderTimes() {
    const container = document.getElementById('times-container');
    container.innerHTML = '';
    
    const times = generateTimeSlots();
    
    times.forEach(time => {
        const btn = document.createElement('button');
        btn.className = 'time-btn';
        btn.textContent = `🕒 ${time}`;
        btn.addEventListener('click', () => selectTime(time));
        container.appendChild(btn);
    });
}

// === ГЕНЕРАЦИЯ СЛОТОВ ВРЕМЕНИ ===
function generateTimeSlots() {
    const times = [];
    const [startHour, startMin] = CONFIG.workingHours.start.split(':').map(Number);
    const [endHour, endMin] = CONFIG.workingHours.end.split(':').map(Number);
    const [lunchStart, lunchEnd] = CONFIG.workingHours.lunch.split('-').map(t => {
        const [h, m] = t.split(':').map(Number);
        return h * 60 + m;
    });
    
    for (let mins = startHour * 60 + startMin; mins < endHour * 60 + endMin; mins += 30) {
        const hour = Math.floor(mins / 60);
        const min = mins % 60;
        
        // Пропускаем обеденный перерыв
        if (mins >= lunchStart && mins < lunchEnd) continue;
        
        times.push(`${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}`);
    }
    
    return times;
}

// === ВЫБОР ВРЕМЕНИ ===
function selectTime(time) {
    state.selectedTime = time;
    state.step = 'confirm';
    
    console.log('✅ Выбрано время:', time);
    showStep('confirm');
    renderConfirm();
}

// === РЕНДЕР ПОДТВЕРЖДЕНИЯ ===
function renderConfirm() {
    document.getElementById('confirm-service').textContent = state.selectedService;
    document.getElementById('confirm-master').textContent = state.selectedMaster;
    document.getElementById('confirm-date').textContent = formatDate(state.selectedDate);
    document.getElementById('confirm-time').textContent = state.selectedTime;
    document.getElementById('confirm-price').textContent = 
        CONFIG.services[state.selectedService] > 0 
            ? CONFIG.services[state.selectedService] + '₽'
            : 'по запросу';
}

// === ПОДТВЕРЖДЕНИЕ И ОТПРАВКА ===
async function confirmBooking() {
    const bookingData = {
        service: state.selectedService,
        master: state.selectedMaster,
        date: state.selectedDate,
        time: state.selectedTime,
        userId: tg.initDataUnsafe.user?.id,
        userName: tg.initDataUnsafe.user?.first_name || 'Клиент',
        price: CONFIG.services[state.selectedService]
    };
    
    console.log('📤 Отправляю бронирование:', bookingData);
    
    try {
        // Отправляем данные в Telegram bot
        if (tg.sendData) {
            tg.sendData(JSON.stringify(bookingData));
        } else {
            // Fallback: отправляем на API
            const response = await fetch('/api/bookings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bookingData)
            });
            
            if (response.ok) {
                console.log('✅ Бронирование подтверждено');
                showStep('success');
                document.getElementById('success-message').textContent = 
                    `Спасибо! Ваша запись: ${state.selectedService} - ${state.selectedTime}`;
            }
        }
    } catch (error) {
        console.error('❌ Ошибка отправки:', error);
        alert('Ошибка при отправке бронирования');
    }
}

// === НАВИГАЦИЯ МЕЖДУ ШАГАМИ ===
function showStep(stepName) {
    document.querySelectorAll('.step').forEach(el => el.classList.add('hidden'));
    document.getElementById(`step-${stepName}`).classList.remove('hidden');
    updateButtons(stepName);
}

// === ОБНОВЛЕНИЕ КНОПОК ===
function updateButtons(step) {
    const btnBack = document.getElementById('btn-back');
    const btnNext = document.getElementById('btn-next');
    const btnConfirm = document.getElementById('btn-confirm');
    const btnDone = document.getElementById('btn-done');
    
    btnBack.classList.toggle('hidden', step === 'service');
    btnNext.classList.toggle('hidden', step === 'confirm' || step === 'success');
    btnConfirm.classList.toggle('hidden', step !== 'confirm');
    btnDone.classList.toggle('hidden', step !== 'success');
}

// === ОБРАБОТЧИКИ КНОПОК ===
function attachEventListeners() {
    document.getElementById('btn-next').addEventListener('click', () => {
        if (state.step === 'service') {
            alert('Выберите услугу');
        } else if (state.step === 'master') {
            alert('Выберите мастера');
        } else if (state.step === 'date') {
            alert('Выберите дату');
        } else if (state.step === 'time') {
            showStep('confirm');
            renderConfirm();
        }
    });
    
    document.getElementById('btn-back').addEventListener('click', goBack);
    document.getElementById('btn-confirm').addEventListener('click', confirmBooking);
    document.getElementById('btn-done').addEventListener('click', () => {
        if (tg.close) tg.close();
    });
}

// === ВОЗВРАТ НАЗАД ===
function goBack() {
    const stepsOrder = ['service', 'master', 'date', 'time', 'confirm'];
    const currentIndex = stepsOrder.indexOf(state.step);
    
    if (currentIndex > 0) {
        state.step = stepsOrder[currentIndex - 1];
        showStep(state.step);
        
        // Рендер предыдущего шага
        if (state.step === 'master') renderMasters();
        if (state.step === 'date') renderCalendar();
        if (state.step === 'time') renderTimes();
    }
}

// === УТИЛИТЫ ===
function highlightActive(type, value) {
    const selector = type === 'service' ? '.service-btn' : 
                     type === 'master' ? '.master-btn' : '.time-btn';
    
    document.querySelectorAll(selector).forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.includes(value)) {
            btn.classList.add('active');
        }
    });
}

function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('ru-RU', { 
        weekday: 'short', 
        day: 'numeric', 
        month: 'long' 
    });
}

function getMonthName(month) {
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    return months[month];
}

// === ЗАПУСК ===
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Инициализация Web App...');
    initTelegram();
    loadData();
});
