/* ==================== УТИЛИТЫ ==================== */

const API = {
    async get(url) {
        const r = await fetch(url);
        return r.json();
    },
    async post(url, data) {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return r.json();
    },
    async put(url, data) {
        const r = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return r.json();
    },
    async del(url) {
        const r = await fetch(url, { method: 'DELETE' });
        return r.json();
    }
};

const GRADE_LABELS = { 5: '5 — Отлично', 4: '4 — Хорошо', 3: '3 — Удовл.', 2: '2 — Неудовл.' };

let selectedRow = null;
let groupsCache = [];
let studentsCache = [];
let subjectsCache = [];
let metaLoaded = false;
let searchTimer = null;

function validatePhone(phone) {
    if (!phone) return true;
    const cleaned = phone.replace(/[\s\-().]/g, '');
    return /^\+?\d{10,15}$/.test(cleaned);
}

function validateEmail(email) {
    if (!email) return true;
    const trimmed = email.trim();
    if (trimmed.length > 254) return false;
    return /^[a-zA-Z0-9._%+\u0400-\u04FF-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$/.test(trimmed);
}

function debounce(fn, ms = 350) {
    return (...args) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => fn(...args), ms);
    };
}

function invalidateMeta() {
    metaLoaded = false;
}

async function loadMeta(force = false) {
    if (metaLoaded && !force) return;
    const meta = await API.get('/api/meta');
    groupsCache = meta.groups;
    studentsCache = meta.students;
    subjectsCache = meta.subjects;
    metaLoaded = true;
    document.getElementById('db-info').textContent =
        `Учеников: ${meta.stats.students} | Предметов: ${meta.stats.subjects} | Оценок: ${meta.stats.grades}`;
}

/* ==================== ДИАЛОГИ ==================== */

const Confirm = {
    _resolve: null,
    ask(message, title = 'Подтверждение') {
        return new Promise(resolve => {
            this._resolve = resolve;
            document.getElementById('confirm-title').textContent = title;
            document.getElementById('confirm-message').textContent = message;
            document.getElementById('confirm-overlay').classList.add('show');
        });
    },
    yes() {
        document.getElementById('confirm-overlay').classList.remove('show');
        if (this._resolve) this._resolve(true);
    },
    no() {
        document.getElementById('confirm-overlay').classList.remove('show');
        if (this._resolve) this._resolve(false);
    }
};

const Alert = {
    show(message, title = 'Информация') {
        return new Promise(resolve => {
            document.getElementById('alert-title').textContent = title;
            document.getElementById('alert-message').textContent = message;
            document.getElementById('alert-overlay').classList.add('show');
            Alert._resolve = resolve;
        });
    },
    close() {
        document.getElementById('alert-overlay').classList.remove('show');
        if (Alert._resolve) Alert._resolve();
    }
};

const About = {
    show() {
        document.getElementById('about-overlay').classList.add('show');
    },
    close() {
        document.getElementById('about-overlay').classList.remove('show');
    }
};

const Modal = {
    open(title, bodyHtml, footerHtml) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = bodyHtml;
        document.getElementById('modal-footer').innerHTML = footerHtml || '';
        document.getElementById('modal-overlay').classList.add('show');
    },
    close() {
        document.getElementById('modal-overlay').classList.remove('show');
    }
};

function selectTableRow(table, tr) {
    table.querySelectorAll('tr.selected').forEach(r => r.classList.remove('selected'));
    if (tr) {
        tr.classList.add('selected');
        selectedRow = tr;
    } else {
        selectedRow = null;
    }
}

function getSelectedId(table) {
    const row = table.querySelector('tr.selected');
    return row ? parseInt(row.dataset.id) : null;
}

function setupTableSelection(table, onDblClick) {
    table.addEventListener('click', e => {
        const tr = e.target.closest('tbody tr');
        if (tr) selectTableRow(table, tr);
    });
    if (onDblClick) {
        table.addEventListener('dblclick', e => {
            const tr = e.target.closest('tbody tr');
            if (tr) onDblClick();
        });
    }
}

function setupSortableTable(table, getData, renderFn) {
    if (table._sortSetup) return;
    table._sortSetup = true;
    let sortCol = null;
    let sortRev = false;
    table.addEventListener('click', e => {
        const th = e.target.closest('th[data-col]');
        if (!th || !table.contains(th)) return;
        const col = th.dataset.col;
        const isNumeric = th.dataset.type === 'number';
        if (sortCol === col) sortRev = !sortRev;
        else { sortCol = col; sortRev = false; }
        const data = getData();
        if (!data || !data.length) return;
        data.sort((a, b) => {
            let va = a[col];
            let vb = b[col];
            if (isNumeric) {
                if (va == null || va === '' || va === '—') va = -1;
                if (vb == null || vb === '' || vb === '—') vb = -1;
                const na = parseFloat(va);
                const nb = parseFloat(vb);
                return sortRev ? nb - na : na - nb;
            }
            va = va == null ? '' : String(va).toLowerCase();
            vb = vb == null ? '' : String(vb).toLowerCase();
            return sortRev ? vb.localeCompare(va) : va.localeCompare(vb);
        });
        renderFn(data);
    });
}

/* ==================== СТУДЕНТЫ ==================== */

const Students = {
    _data: [],

    async refresh() {
        if (!metaLoaded) await loadMeta();

        const search = document.getElementById('student-search').value.trim();
        const groupName = document.getElementById('student-group-filter').value;
        const status = document.getElementById('student-status-filter').value;

        const groupSelect = document.getElementById('student-group-filter');
        const curGroup = groupSelect.value;
        groupSelect.innerHTML = '<option>Все</option>' +
            groupsCache.map(g => `<option>${g.name}</option>`).join('');
        if ([...groupSelect.options].some(o => o.value === curGroup)) groupSelect.value = curGroup;

        let url = '/api/students?';
        if (search) url += `search=${encodeURIComponent(search)}&`;
        else {
            if (groupName !== 'Все') {
                const g = groupsCache.find(g => g.name === groupName);
                if (g) url += `group_id=${g.id}&`;
            }
            if (status !== 'Все') url += `status=${encodeURIComponent(status)}&`;
        }

        this._data = await API.get(url);
        this._render(this._data);
        document.getElementById('students-status').textContent = `Учеников: ${this._data.length}`;
    },

    _render(data) {
        const tbody = document.querySelector('#students-table tbody');
        tbody.innerHTML = data.map((s, i) => {
            let cls = '';
            if (s.status === 'Отчислен') cls = 'text-expelled';
            else if (s.status === 'Академический отпуск') cls = 'text-leave';
            const avg = s.avg_grade ? s.avg_grade.toFixed(2) : '—';
            return `<tr data-id="${s.id}" class="${cls}">
                <td>${i + 1}</td><td>${s.student_id}</td>
                <td>${s.last_name}</td><td>${s.first_name}</td>
                <td>${s.middle_name || ''}</td><td>${s.group_name}</td>
                <td>${s.birth_date_fmt || ''}</td><td>${s.email || ''}</td>
                <td>${s.phone || ''}</td><td>${s.status}</td><td>${avg}</td>
            </tr>`;
        }).join('');
    },

    async add() { this._openDialog(); },
    async edit() {
        const id = getSelectedId(document.getElementById('students-table'));
        if (!id) { await Alert.show('Выберите студента!', 'Предупреждение'); return; }
        const student = await API.get(`/api/students/${id}`);
        this._openDialog(student);
    },
    async remove() {
        const id = getSelectedId(document.getElementById('students-table'));
        if (!id) { await Alert.show('Выберите студента!', 'Предупреждение'); return; }
        const student = await API.get(`/api/students/${id}`);
        const name = `${student.last_name} ${student.first_name}`;
        if (await Confirm.ask(`Удалить студента '${name}'?\nВсе его оценки будут удалены!`)) {
            await API.del(`/api/students/${id}`);
            invalidateMeta();
            this.refresh();
        }
    },

    _openDialog(student = null) {
        const groups = groupsCache.length ? groupsCache : [];
        const isEdit = !!student;
        const body = `
            <div class="form-row"><label>Фамилия:*</label><input id="f-last_name" value="${student?.last_name || ''}"></div>
            <div class="form-row"><label>Имя:*</label><input id="f-first_name" value="${student?.first_name || ''}"></div>
            <div class="form-row"><label>Отчество:</label><input id="f-middle_name" value="${student?.middle_name || ''}"></div>
            <div class="form-row"><label>№ Зачётки:*</label><input id="f-student_id" value="${student?.student_id || ''}"></div>
            <div class="form-row"><label>Дата рождения:</label><input id="f-birth_date" placeholder="ДД.ММ.ГГГГ" value="${student?.birth_date ? formatDateDisplay(student.birth_date) : ''}"></div>
            <div class="form-row"><label>Email:</label><input id="f-email" placeholder="белова57@school15.edu.ru" value="${student?.email || ''}"></div>
            <div class="form-row"><label>Телефон:</label><input id="f-phone" placeholder="+79001234567" value="${student?.phone || ''}"></div>
            <div class="form-row"><label>Группа:*</label>
                <select id="f-group_id">${groups.map(g =>
                    `<option value="${g.id}" ${student?.group_id === g.id ? 'selected' : ''}>${g.name}</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Статус:</label>
                <select id="f-status">
                    ${['Активный','Академический отпуск','Отчислен','Выпускник'].map(s =>
                        `<option ${(student?.status || 'Активный') === s ? 'selected' : ''}>${s}</option>`
                    ).join('')}
                </select>
            </div>`;
        const footer = `
            <button class="btn" onclick="Modal.close()">✗ Отмена</button>
            <button class="btn btn-primary" id="modal-save">✓ Сохранить</button>`;
        Modal.open(isEdit ? 'Редактировать студента' : 'Добавить студента', body, footer);
        document.getElementById('modal-save').onclick = async () => {
            const data = {
                last_name: document.getElementById('f-last_name').value.trim(),
                first_name: document.getElementById('f-first_name').value.trim(),
                middle_name: document.getElementById('f-middle_name').value.trim(),
                student_id: document.getElementById('f-student_id').value.trim(),
                birth_date: document.getElementById('f-birth_date').value.trim(),
                email: document.getElementById('f-email').value.trim(),
                phone: document.getElementById('f-phone').value.trim(),
                group_id: parseInt(document.getElementById('f-group_id').value),
                status: document.getElementById('f-status').value
            };
            if (!validateEmail(data.email)) {
                await Alert.show('Некорректный email! Пример: белова57@school15.edu.ru', 'Ошибка');
                return;
            }
            if (!validatePhone(data.phone)) {
                await Alert.show('Некорректный телефон! Только цифры, 10–15 знаков (например: +79001234567)', 'Ошибка');
                return;
            }
            const url = isEdit ? `/api/students/${student.id}` : '/api/students';
            const method = isEdit ? API.put : API.post;
            const res = await method(url, data);
            if (res.ok) { Modal.close(); invalidateMeta(); Students.refresh(); }
            else await Alert.show(res.error, 'Ошибка');
        };
    }
};

/* ==================== ПРЕДМЕТЫ ==================== */

const Subjects = {
    _data: [],

    async refresh() {
        this._data = await API.get('/api/subjects');
        subjectsCache = this._data;
        this._render(this._data);
        document.getElementById('subjects-status').textContent = `Предметов: ${this._data.length}`;
    },

    _render(data) {
        const tbody = document.querySelector('#subjects-table tbody');
        tbody.innerHTML = data.map((s, i) => `<tr data-id="${s.id}">
            <td>${i + 1}</td><td>${s.name}</td><td>${s.short_name || ''}</td>
            <td>${s.teacher || ''}</td><td>${s.hours || 0}</td>
            <td>${s.semester}</td><td>${s.course}</td><td>${s.subject_type}</td>
        </tr>`).join('');
    },

    async add() { this._openDialog(); },
    async edit() {
        const id = getSelectedId(document.getElementById('subjects-table'));
        if (!id) { await Alert.show('Выберите предмет!', 'Предупреждение'); return; }
        const subject = subjectsCache.find(s => s.id === id);
        this._openDialog(subject);
    },
    async remove() {
        const id = getSelectedId(document.getElementById('subjects-table'));
        if (!id) { await Alert.show('Выберите предмет!', 'Предупреждение'); return; }
        if (await Confirm.ask('Удалить предмет? Все связанные оценки будут удалены!')) {
            await API.del(`/api/subjects/${id}`);
            invalidateMeta();
            this.refresh();
        }
    },

    _openDialog(subject = null) {
        const isEdit = !!subject;
        const body = `
            <div class="form-row"><label>Название:*</label><input id="f-name" value="${subject?.name || ''}"></div>
            <div class="form-row"><label>Аббревиатура:</label><input id="f-short_name" value="${subject?.short_name || ''}"></div>
            <div class="form-row"><label>Преподаватель:</label><input id="f-teacher" value="${subject?.teacher || ''}"></div>
            <div class="form-row"><label>Часов:</label><input id="f-hours" type="number" value="${subject?.hours || 0}"></div>
            <div class="form-row"><label>Семестр:</label>
                <select id="f-semester">${[1,2,3,4,5,6,7,8].map(n =>
                    `<option value="${n}" ${(subject?.semester || 1) === n ? 'selected' : ''}>${n}</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Класс:</label>
                <select id="f-course">${[1,2,3,4,5,6,7,8,9,10,11].map(n =>
                    `<option value="${n}" ${(subject?.course || 1) === n ? 'selected' : ''}>${n}</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Тип:</label>
                <select id="f-subject_type">
                    ${['Урок','Практика','Лабораторная','Семинар'].map(t =>
                        `<option ${(subject?.subject_type || 'Урок') === t ? 'selected' : ''}>${t}</option>`
                    ).join('')}
                </select>
            </div>`;
        const footer = `
            <button class="btn" onclick="Modal.close()">✗ Отмена</button>
            <button class="btn btn-primary" id="modal-save">✓ Сохранить</button>`;
        Modal.open(isEdit ? 'Редактировать предмет' : 'Добавить предмет', body, footer);
        document.getElementById('modal-save').onclick = async () => {
            const data = {
                name: document.getElementById('f-name').value.trim(),
                short_name: document.getElementById('f-short_name').value.trim(),
                teacher: document.getElementById('f-teacher').value.trim(),
                hours: document.getElementById('f-hours').value,
                semester: document.getElementById('f-semester').value,
                course: document.getElementById('f-course').value,
                subject_type: document.getElementById('f-subject_type').value
            };
            const url = isEdit ? `/api/subjects/${subject.id}` : '/api/subjects';
            const method = isEdit ? API.put : API.post;
            const res = await method(url, data);
            if (res.ok) { Modal.close(); invalidateMeta(); Subjects.refresh(); }
            else await Alert.show(res.error, 'Ошибка');
        };
    }
};

/* ==================== ОЦЕНКИ ==================== */

const Grades = {
    _data: [],

    async refresh() {
        await loadMeta();

        const stSel = document.getElementById('grade-student-filter');
        const curSt = stSel.value;
        stSel.innerHTML = '<option>Все</option>' + studentsCache.map(s =>
            `<option>${s.last_name} ${s.first_name} (${s.student_id})</option>`
        ).join('');
        if ([...stSel.options].some(o => o.value === curSt)) stSel.value = curSt;

        const subSel = document.getElementById('grade-subject-filter');
        const curSub = subSel.value;
        subSel.innerHTML = '<option>Все</option>' + subjectsCache.map(s =>
            `<option>${s.name}</option>`
        ).join('');
        if ([...subSel.options].some(o => o.value === curSub)) subSel.value = curSub;

        let url = '/api/grades?limit=300&';
        if (stSel.value !== 'Все') {
            const s = studentsCache.find(s => `${s.last_name} ${s.first_name} (${s.student_id})` === stSel.value);
            if (s) url += `student_id=${s.id}&`;
        }
        if (subSel.value !== 'Все') {
            const s = subjectsCache.find(s => s.name === subSel.value);
            if (s) url += `subject_id=${s.id}&`;
        }
        const sem = document.getElementById('grade-semester-filter').value;
        if (sem !== 'Все') url += `semester=${sem}&`;

        const resp = await API.get(url);
        this._data = resp.rows || resp;
        this._render(this._data);
        const total = resp.total ?? this._data.length;
        const shown = resp.shown ?? this._data.length;
        const status = total > shown
            ? `Показано: ${shown} из ${total} (используйте фильтры)`
            : `Записей: ${total}`;
        document.getElementById('grades-status').textContent = status;
    },

    _render(data) {
        const tbody = document.querySelector('#grades-table tbody');
        tbody.innerHTML = data.map((g, i) => `<tr data-id="${g.id}" class="grade-${g.grade}">
            <td>${i + 1}</td>
            <td>${g.student_name.trim()}</td>
            <td>${g.group_name}</td>
            <td>${g.subject_name}</td>
            <td>${GRADE_LABELS[g.grade] || g.grade}</td>
            <td>${g.grade_type}</td>
            <td>${g.date_fmt}</td>
            <td>${g.semester}</td>
            <td>${g.teacher || ''}</td>
        </tr>`).join('');
    },

    async add() { this._openDialog(); },
    async edit() {
        const id = getSelectedId(document.getElementById('grades-table'));
        if (!id) { await Alert.show('Выберите запись!', 'Предупреждение'); return; }
        let grade = this._data.find(g => g.id === id);
        if (!grade) grade = await API.get(`/api/grades/${id}`);
        this._openDialog(grade);
    },
    async remove() {
        const id = getSelectedId(document.getElementById('grades-table'));
        if (!id) { await Alert.show('Выберите запись!', 'Предупреждение'); return; }
        if (await Confirm.ask('Удалить выбранную оценку?')) {
            await API.del(`/api/grades/${id}`);
            invalidateMeta();
            this.refresh();
        }
    },

    _openDialog(grade = null) {
        const isEdit = !!grade;
        const today = new Date();
        const todayStr = `${String(today.getDate()).padStart(2,'0')}.${String(today.getMonth()+1).padStart(2,'0')}.${today.getFullYear()}`;
        const body = `
            <div class="form-row"><label>Студент:*</label>
                <select id="f-student_id">${studentsCache.map(s =>
                    `<option value="${s.id}" ${grade?.student_id === s.id ? 'selected' : ''}>${s.last_name} ${s.first_name} (${s.student_id})</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Предмет:*</label>
                <select id="f-subject_id">${subjectsCache.map(s =>
                    `<option value="${s.id}" ${grade?.subject_id === s.id ? 'selected' : ''}>${s.name}</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Оценка:*</label>
                <div class="radio-group">
                    ${[5,4,3,2].map(v => `<label><input type="radio" name="grade" value="${v}" ${(grade?.grade || 5) === v ? 'checked' : ''}> ${v}</label>`).join('')}
                </div>
            </div>
            <div class="form-row"><label>Тип:*</label>
                <select id="f-grade_type">
                    ${['Четверть','Контрольная работа','Самостоятельная работа','Диктант','Проверочная работа'].map(t =>
                        `<option ${(grade?.grade_type || 'Четверть') === t ? 'selected' : ''}>${t}</option>`
                    ).join('')}
                </select>
            </div>
            <div class="form-row"><label>Дата:*</label>
                <input id="f-date" value="${grade ? formatDateDisplay(grade.date) : todayStr}">
            </div>
            <div class="form-row"><label>Семестр:*</label>
                <select id="f-semester">${[1,2,3,4,5,6,7,8].map(n =>
                    `<option value="${n}" ${(grade?.semester || 1) === n ? 'selected' : ''}>${n}</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Преподаватель:</label>
                <input id="f-teacher" value="${grade?.teacher || ''}">
            </div>`;
        const footer = `
            <button class="btn" onclick="Modal.close()">✗ Отмена</button>
            <button class="btn btn-primary" id="modal-save">✓ Сохранить</button>`;
        Modal.open(isEdit ? 'Редактировать оценку' : 'Добавить оценку', body, footer);
        document.getElementById('modal-save').onclick = async () => {
            const gradeVal = document.querySelector('input[name="grade"]:checked');
            if (!gradeVal) { await Alert.show('Выберите оценку!', 'Ошибка'); return; }
            const data = {
                student_id: parseInt(document.getElementById('f-student_id').value),
                subject_id: parseInt(document.getElementById('f-subject_id').value),
                grade: parseInt(gradeVal.value),
                grade_type: document.getElementById('f-grade_type').value,
                date: document.getElementById('f-date').value.trim(),
                semester: document.getElementById('f-semester').value,
                teacher: document.getElementById('f-teacher').value.trim()
            };
            const url = isEdit ? `/api/grades/${grade.id}` : '/api/grades';
            const method = isEdit ? API.put : API.post;
            const res = await method(url, data);
            if (res.ok) { Modal.close(); invalidateMeta(); Grades.refresh(); }
            else await Alert.show(res.error, 'Ошибка');
        };
    }
};

/* ==================== ОТЧЁТЫ ==================== */

const Reports = {
    _data: [],
    _keys: [],
    _numericKeys: new Set(['grades_count', 'avg', 'fives', 'fours', 'threes', 'twos', 'total_grades', 'grade', 'count', 'semester', 'debt_count']),

    async updateParams() {
        await loadMeta();
        const report = document.querySelector('input[name="report-type"]:checked').value;
        const frame = document.getElementById('report-params');
        frame.innerHTML = '';

        if (['group_stat', 'excellent', 'failing'].includes(report)) {
            frame.innerHTML += `<label>Группа:</label>
                <select id="param-group"><option>Все</option>
                ${groupsCache.map(g => `<option>${g.name}</option>`).join('')}
                </select>`;
        }
        if (report === 'group_stat') {
            frame.innerHTML += `<label style="margin-top:8px;display:block">Семестр:</label>
                <select id="param-semester">
                    <option>Все</option>${[1,2,3,4,5,6,7,8].map(n => `<option>${n}</option>`).join('')}
                </select>`;
        }
        if (report === 'student_card') {
            frame.innerHTML += `<label>Ученик:</label>
                <select id="param-student">
                ${studentsCache.map(s => `<option value="${s.id}">${s.last_name} ${s.first_name} (${s.student_id})</option>`).join('')}
                </select>`;
        }
    },

    _getParams() {
        const report = document.querySelector('input[name="report-type"]:checked').value;
        let params = `report=${report}`;
        const groupEl = document.getElementById('param-group');
        if (groupEl && groupEl.value !== 'Все') {
            const g = groupsCache.find(g => g.name === groupEl.value);
            if (g) params += `&group_id=${g.id}`;
        }
        const semEl = document.getElementById('param-semester');
        if (semEl && semEl.value !== 'Все') params += `&semester=${semEl.value}`;
        const stEl = document.getElementById('param-student');
        if (stEl) params += `&student_id=${stEl.value}`;
        return { report, params };
    },

    async generate() {
        const { report, params } = this._getParams();
        const data = await API.get(`/api/reports/${report}?${params}`);
        const groupEl = document.getElementById('param-group');
        const allGroups = report === 'group_stat' && (!groupEl || groupEl.value === 'Все');
        const configs = {
            group_stat: {
                heads: allGroups
                    ? ['ФИО', 'Класс', '№ Зачётки', 'Оценок', 'Ср. балл', '5', '4', '3', '2']
                    : ['ФИО', '№ Зачётки', 'Оценок', 'Ср. балл', '5', '4', '3', '2'],
                keys: allGroups
                    ? ['name', 'group_name', 'student_number', 'grades_count', 'avg', 'fives', 'fours', 'threes', 'twos']
                    : ['name', 'student_number', 'grades_count', 'avg', 'fives', 'fours', 'threes', 'twos']
            },
            subject_stat: {
                heads: ['Предмет','Оценок','Ср. балл','5','4','3','2'],
                keys: ['subject_name','total_grades','avg','fives','fours','threes','twos']
            },
            excellent: {
                heads: ['ФИО','№ Зачётки','Группа','Ср. балл','Оценок'],
                keys: ['name','student_number','group_name','avg','grades_count']
            },
            failing: {
                heads: ['ФИО','№ Зачётки','Группа','Долгов'],
                keys: ['name','student_number','group_name','debt_count']
            },
            distribution: {
                heads: ['Оценка','Словесно','Количество','Процент'],
                keys: ['grade','label','count','percent']
            },
            student_card: {
                heads: ['Предмет','Оценка','Тип','Дата','Семестр','Преподаватель'],
                keys: ['subject_name','grade','grade_type','date','semester','teacher']
            }
        };
        const cfg = configs[report];
        this._keys = cfg.keys;
        this._data = data.rows || [];
        const thead = document.querySelector('#reports-table thead tr');
        thead.innerHTML = cfg.heads.map((h, i) =>
            `<th data-col="${cfg.keys[i]}"${this._numericKeys.has(cfg.keys[i]) ? ' data-type="number"' : ''}>${h}</th>`
        ).join('');
        this._render(this._data);
        document.getElementById('report-info').textContent = data.info || '';
    },

    _render(data) {
        const tbody = document.querySelector('#reports-table tbody');
        tbody.innerHTML = data.map(row => {
            let cls = '';
            if (row.tag === 'excellent') cls = 'text-excellent';
            else if (row.tag === 'failing') cls = 'text-failing';
            const style = row.color ? `style="color:${row.color}"` : '';
            return `<tr class="${cls}" ${style}>${this._keys.map(k => `<td>${row[k] ?? ''}</td>`).join('')}</tr>`;
        }).join('');
    },

    async exportCsv() {
        const btn = document.getElementById('btn-export-csv');
        const { params } = this._getParams();
        const prevText = btn ? btn.textContent : '';
        try {
            if (btn) {
                btn.disabled = true;
                btn.textContent = '⏳ Экспорт...';
            }
            const res = await fetch(`/api/reports/export?${params}`);
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                await Alert.show(err.error || 'Не удалось экспортировать отчёт', 'Ошибка');
                return;
            }
            const blob = await res.blob();
            const disp = res.headers.get('Content-Disposition') || '';
            let filename = 'otchet.csv';
            try {
                const utfMatch = disp.match(/filename\*=UTF-8''([^;]+)/i);
                const plainMatch = disp.match(/filename="([^"]+)"/i);
                if (utfMatch) filename = decodeURIComponent(utfMatch[1]);
                else if (plainMatch) filename = plainMatch[1];
            } catch (_) {
                /* оставляем имя по умолчанию */
            }

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (e) {
            await Alert.show(e?.message || 'Не удалось скачать файл. Перезапустите сайт и попробуйте снова.', 'Ошибка');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = prevText;
            }
        }
    }
};

/* ==================== ГРУППЫ ==================== */

const Groups = {
    async showManager() {
        groupsCache = await API.get('/api/groups');
        const body = `
            <div class="toolbar">
                <button class="btn" onclick="Groups.add()">➕ Добавить</button>
                <button class="btn" onclick="Groups.edit()">✏️ Редактировать</button>
                <button class="btn" onclick="Groups.remove()">🗑️ Удалить</button>
            </div>
            <div class="groups-table-wrap">
                <table id="groups-table">
                    <thead><tr><th>№</th><th>Класс</th><th>Параллель</th><th>Звено</th></tr></thead>
                    <tbody>${groupsCache.map((g, i) => `<tr data-id="${g.id}">
                        <td>${i + 1}</td><td>${g.name}</td><td>${g.course}</td><td>${g.faculty}</td>
                    </tr>`).join('')}</tbody>
                </table>
            </div>`;
        Modal.open('Управление классами', body, '<button class="btn" onclick="Modal.close()">Закрыть</button>');
        setupTableSelection(document.getElementById('groups-table'), () => Groups.edit());
    },

    async refresh() {
        groupsCache = await API.get('/api/groups');
        const tbody = document.querySelector('#groups-table tbody');
        if (tbody) {
            tbody.innerHTML = groupsCache.map((g, i) => `<tr data-id="${g.id}">
                <td>${i + 1}</td><td>${g.name}</td><td>${g.course}</td><td>${g.faculty}</td>
            </tr>`).join('');
        }
    },

    async add() { this._openDialog(); },
    async edit() {
        const id = getSelectedId(document.getElementById('groups-table'));
        if (!id) { await Alert.show('Выберите класс!', 'Предупреждение'); return; }
        const group = groupsCache.find(g => g.id === id);
        this._openDialog(group);
    },
    async remove() {
        const id = getSelectedId(document.getElementById('groups-table'));
        if (!id) { await Alert.show('Выберите класс!', 'Предупреждение'); return; }
        if (await Confirm.ask('Удалить класс?')) {
            const res = await API.del(`/api/groups/${id}`);
            if (res.ok) { this.refresh(); invalidateMeta(); Students.refresh(); }
            else await Alert.show(`Нельзя удалить класс: ${res.error}`, 'Ошибка');
        }
    },

    _openDialog(group = null) {
        const isEdit = !!group;
        const body = `
            <div class="form-row"><label>Название класса:*</label><input id="f-name" placeholder="Например: 5А" value="${group?.name || ''}"></div>
            <div class="form-row"><label>Параллель:*</label>
                <select id="f-course">${[1,2,3,4,5,6,7,8,9,10,11].map(n =>
                    `<option value="${n}" ${(group?.course || 5) === n ? 'selected' : ''}>${n} класс</option>`
                ).join('')}</select>
            </div>
            <div class="form-row"><label>Звено:*</label>
                <select id="f-faculty">
                    ${['Начальная школа','Среднее звено','Старшие классы'].map(f =>
                        `<option ${(group?.faculty || 'Среднее звено') === f ? 'selected' : ''}>${f}</option>`
                    ).join('')}
                </select>
            </div>`;
        const footer = `
            <button class="btn" onclick="Groups.showManager()">✗ Отмена</button>
            <button class="btn btn-primary" id="modal-save">✓ Сохранить</button>`;
        Modal.open(isEdit ? 'Редактировать класс' : 'Добавить класс', body, footer);
        document.getElementById('modal-save').onclick = async () => {
            const data = {
                name: document.getElementById('f-name').value.trim(),
                course: document.getElementById('f-course').value,
                faculty: document.getElementById('f-faculty').value
            };
            const url = isEdit ? `/api/groups/${group.id}` : '/api/groups';
            const method = isEdit ? API.put : API.post;
            const res = await method(url, data);
            if (res.ok) { Groups.showManager(); invalidateMeta(); Students.refresh(); }
            else await Alert.show(res.error, 'Ошибка');
        };
    }
};

/* ==================== МЕНЮ ==================== */

function setupMenu() {
    document.querySelectorAll('.dropdown a').forEach(a => {
        a.addEventListener('click', async e => {
            e.preventDefault();
            const action = a.dataset.action;
            if (action === 'manage-groups') Groups.showManager();
            else if (action === 'exit') {
                if (await Confirm.ask('Выйти из программы?')) window.close();
            }
            else if (action === 'load-demo') {
                if (await Confirm.ask('Загрузить демо-данные?\nТекущие данные будут удалены и заменены.')) {
                    const res = await API.post('/api/demo', {});
                    if (res.ok) {
                        const s = res.stats || {};
                        await Alert.show(
                            `Демо-данные загружены!\n\n` +
                            `Классов: ${s.groups ?? '—'}\n` +
                            `Предметов: ${s.subjects ?? '—'}\n` +
                            `Учеников: ${s.students ?? '—'}\n` +
                            `Оценок: ${s.grades ?? '—'}`
                        );
                        invalidateMeta();
                        refreshAll();
                    } else await Alert.show(res.error, 'Ошибка');
                }
            }
            else if (action === 'clear-data') {
                if (await Confirm.ask('УДАЛИТЬ ВСЕ ДАННЫЕ?\nЭто действие необратимо!', 'Очистка')) {
                    if (await Confirm.ask('Вы уверены? Все данные будут потеряны!', 'Подтверждение')) {
                        await API.post('/api/clear', {});
                        await Alert.show('Все данные удалены');
                        invalidateMeta();
                        refreshAll();
                    }
                }
            }
            else if (action === 'about') {
                About.show();
            }
        });
    });
}

/* ==================== ОБЩЕЕ ==================== */

function formatDateDisplay(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length === 3) return `${parts[2]}.${parts[1]}.${parts[0]}`;
    return dateStr;
}

function updateClock() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    document.getElementById('clock').textContent =
        `${pad(now.getDate())}.${pad(now.getMonth()+1)}.${now.getFullYear()}  ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

async function updateDbInfo() {
    try {
        const stats = await API.get('/api/stats');
        document.getElementById('db-info').textContent =
            `Учеников: ${stats.students} | Предметов: ${stats.subjects} | Оценок: ${stats.grades}`;
    } catch {}
}

function refreshAll() {
    invalidateMeta();
    document.getElementById('student-search').value = '';
    document.getElementById('student-group-filter').value = 'Все';
    document.getElementById('student-status-filter').value = 'Все';
    document.getElementById('grade-student-filter').value = 'Все';
    document.getElementById('grade-subject-filter').value = 'Все';
    document.getElementById('grade-semester-filter').value = 'Все';
    Students.refresh();
    Subjects.refresh();
    Grades.refresh();
    updateDbInfo();
}

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
            document.getElementById('status-text').textContent = `Раздел: ${tab.textContent}`;
            if (tab.dataset.tab === 'reports') Reports.generate();
        });
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    setupTabs();
    setupMenu();
    setupTableSelection(document.getElementById('students-table'), () => Students.edit());
    setupTableSelection(document.getElementById('subjects-table'), () => Subjects.edit());
    setupTableSelection(document.getElementById('grades-table'), () => Grades.edit());
    setupSortableTable(
        document.getElementById('students-table'),
        () => Students._data,
        d => Students._render(d)
    );
    setupSortableTable(
        document.getElementById('subjects-table'),
        () => Subjects._data,
        d => Subjects._render(d)
    );
    setupSortableTable(
        document.getElementById('grades-table'),
        () => Grades._data,
        d => Grades._render(d)
    );
    setupSortableTable(
        document.getElementById('reports-table'),
        () => Reports._data,
        d => Reports._render(d)
    );
    document.getElementById('student-search').addEventListener('input', debounce(() => Students.refresh()));
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(updateDbInfo, 15000);

    const seed = await API.post('/api/demo/seed-if-empty', {});
    if (seed.seeded) invalidateMeta();

    await loadMeta(true);
    await Students.refresh();
    await Subjects.refresh();
    await Grades.refresh();
    Reports.updateParams();
    Reports.generate();
});
