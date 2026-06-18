import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils import validate_email, validate_phone, parse_date, format_date


class GroupDialog(tk.Toplevel):
    def __init__(self, parent, db, group=None):
        super().__init__(parent)
        self.db = db
        self.group = group
        self.result = None

        self.title("Редактировать группу" if group else "Добавить группу")
        self.geometry("400x280")
        self.resizable(False, False)
        self.configure(bg='#f0f0f0')
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        if group:
            self._fill_data()
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - self.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Название группы:*").grid(row=0, column=0, sticky='w', pady=10)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(main_frame, text="Курс:*").grid(row=1, column=0, sticky='w', pady=10)
        self.course_var = tk.StringVar(value="1")
        ttk.Combobox(main_frame, textvariable=self.course_var,
                     values=["1", "2", "3", "4", "5", "6"],
                     width=28, state='readonly').grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(main_frame, text="Факультет:*").grid(row=2, column=0, sticky='w', pady=10)
        self.faculty_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.faculty_var, width=30).grid(row=2, column=1, padx=10, pady=10)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20, sticky='e')

        ttk.Button(btn_frame, text="✗ Отмена", command=self.destroy).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✓ Сохранить", command=self._save).pack(side='left')

    def _fill_data(self):
        self.name_var.set(self.group['name'])
        self.course_var.set(str(self.group['course']))
        self.faculty_var.set(self.group['faculty'])

    def _save(self):
        name = self.name_var.get().strip()
        course = self.course_var.get()
        faculty = self.faculty_var.get().strip()

        if not all([name, course, faculty]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля!", parent=self)
            return

        try:
            if self.group:
                self.db.update_group(self.group['id'], name, int(course), faculty)
            else:
                self.db.add_group(name, int(course), faculty)
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}", parent=self)


class StudentDialog(tk.Toplevel):
    def __init__(self, parent, db, student=None):
        super().__init__(parent)
        self.db = db
        self.student = student
        self.result = None
        self.placeholder = "ДД.ММ.ГГГГ"

        self.title("Редактировать студента" if student else "Добавить студента")
        self.geometry("500x500")
        self.resizable(False, False)
        self.configure(bg='#f0f0f0')
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        if student:
            self._fill_data()
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - self.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        fields = [
            ("Фамилия:*", "last_name"),
            ("Имя:*", "first_name"),
            ("Отчество:", "middle_name"),
            ("№ Зачётки:*", "student_id"),
            ("Дата рождения:", "birth_date"),
            ("Email:", "email"),
            ("Телефон:", "phone"),
        ]

        self.vars = {}
        self.entries = {}

        for i, (label, key) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            var = tk.StringVar()
            self.vars[key] = var

            entry = ttk.Entry(main_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky='ew', padx=(10, 0), pady=5)
            self.entries[key] = entry

            # Спец-обработка для даты (плейсхолдер)
            if key == 'birth_date':
                var.set(self.placeholder)
                entry.configure(foreground='gray')
                entry.bind('<FocusIn>', self._on_date_focus_in)
                entry.bind('<FocusOut>', self._on_date_focus_out)

        # Группа
        row_idx = len(fields)
        ttk.Label(main_frame, text="Группа:*").grid(row=row_idx, column=0, sticky='w', pady=5)
        self.group_var = tk.StringVar()
        self.groups = self.db.get_all_groups()
        group_names = [g['name'] for g in self.groups]
        self.group_combo = ttk.Combobox(main_frame, textvariable=self.group_var,
                                         values=group_names, state='readonly')
        self.group_combo.grid(row=row_idx, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=row_idx + 1, column=0, sticky='w', pady=5)
        self.status_var = tk.StringVar(value="Активный")
        ttk.Combobox(main_frame, textvariable=self.status_var,
                     values=["Активный", "Академический отпуск", "Отчислен", "Выпускник"],
                     state='readonly').grid(row=row_idx + 1, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row_idx + 2, column=0, columnspan=2, pady=(20, 0), sticky='e')

        ttk.Button(btn_frame, text="✗ Отмена", command=self.destroy).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✓ Сохранить", command=self._save).pack(side='left')

    def _on_date_focus_in(self, event):
        if self.vars['birth_date'].get() == self.placeholder:
            self.vars['birth_date'].set("")
            self.entries['birth_date'].configure(foreground='black')

    def _on_date_focus_out(self, event):
        if not self.vars['birth_date'].get().strip():
            self.vars['birth_date'].set(self.placeholder)
            self.entries['birth_date'].configure(foreground='gray')

    def _fill_data(self):
        for key in ['last_name', 'first_name', 'middle_name', 'student_id', 'email', 'phone']:
            self.vars[key].set(self.student[key] or '')

        self.status_var.set(self.student['status'])

        if self.student['birth_date']:
            self.vars['birth_date'].set(format_date(self.student['birth_date']))
            self.entries['birth_date'].configure(foreground='black')

        for g in self.groups:
            if g['id'] == self.student['group_id']:
                self.group_var.set(g['name'])
                break

    def _save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}

        if data['birth_date'] == self.placeholder:
            data['birth_date'] = ""

        if not all([data['last_name'], data['first_name'], data['student_id'], self.group_var.get()]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля!", parent=self)
            return

        if data['email'] and not validate_email(data['email']):
            messagebox.showerror("Ошибка", "Некорректный email!", parent=self)
            return

        if data['phone'] and not validate_phone(data['phone']):
            messagebox.showerror("Ошибка", "Некорректный телефон! Только цифры, 10–15 знаков", parent=self)
            return

        birth_date = None
        if data['birth_date']:
            birth_date = parse_date(data['birth_date'])
            if not birth_date:
                messagebox.showerror("Ошибка", "Формат даты: ДД.ММ.ГГГГ", parent=self)
                return

        group_id = next((g['id'] for g in self.groups if g['name'] == self.group_var.get()), None)

        try:
            if self.student:
                self.db.update_student(
                    self.student['id'], data['last_name'], data['first_name'], data['middle_name'],
                    group_id, data['student_id'], birth_date, data['email'], data['phone'], self.status_var.get()
                )
            else:
                self.db.add_student(
                    data['last_name'], data['first_name'], data['middle_name'], group_id,
                    data['student_id'], birth_date, data['email'], data['phone'], self.status_var.get()
                )
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}", parent=self)


class SubjectDialog(tk.Toplevel):
    def __init__(self, parent, db, subject=None):
        super().__init__(parent)
        self.db = db
        self.subject = subject
        self.result = None

        self.title("Редактировать предмет" if subject else "Добавить предмет")
        self.geometry("450x420")
        self.resizable(False, False)
        self.configure(bg='#f0f0f0')
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        if subject:
            self._fill_data()
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - self.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        fields = [
            ("Название:*", "name"),
            ("Аббревиатура:", "short_name"),
            ("Преподаватель:", "teacher"),
            ("Часов:", "hours"),
        ]

        self.vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            var = tk.StringVar()
            self.vars[key] = var
            ttk.Entry(main_frame, textvariable=var).grid(row=i, column=1, sticky='ew', padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="Семестр:").grid(row=4, column=0, sticky='w', pady=5)
        self.semester_var = tk.StringVar(value="1")
        ttk.Combobox(main_frame, textvariable=self.semester_var,
                     values=[str(i) for i in range(1, 9)], state='readonly').grid(row=4, column=1, sticky='ew', padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="Курс:").grid(row=5, column=0, sticky='w', pady=5)
        self.course_var = tk.StringVar(value="1")
        ttk.Combobox(main_frame, textvariable=self.course_var,
                     values=[str(i) for i in range(1, 7)], state='readonly').grid(row=5, column=1, sticky='ew', padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="Тип:").grid(row=6, column=0, sticky='w', pady=5)
        self.type_var = tk.StringVar(value="Лекция")
        ttk.Combobox(main_frame, textvariable=self.type_var,
                     values=["Лекция", "Практика", "Лабораторная", "Семинар"],
                     state='readonly').grid(row=6, column=1, sticky='ew', padx=(10, 0), pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0), sticky='e')

        ttk.Button(btn_frame, text="✗ Отмена", command=self.destroy).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✓ Сохранить", command=self._save).pack(side='left')

    def _fill_data(self):
        for key in ['name', 'short_name', 'teacher']:
            self.vars[key].set(self.subject[key] or '')
        self.vars['hours'].set(str(self.subject['hours'] or 0))
        self.semester_var.set(str(self.subject['semester']))
        self.course_var.set(str(self.subject['course']))
        self.type_var.set(self.subject['subject_type'])

    def _save(self):
        name = self.vars['name'].get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название!", parent=self)
            return

        try:
            hours = int(self.vars['hours'].get() or 0)
            if self.subject:
                self.db.update_subject(self.subject['id'], name, self.vars['short_name'].get(), self.vars['teacher'].get(),
                                       hours, int(self.semester_var.get()), int(self.course_var.get()), self.type_var.get())
            else:
                self.db.add_subject(name, self.vars['short_name'].get(), self.vars['teacher'].get(),
                                    hours, int(self.semester_var.get()), int(self.course_var.get()), self.type_var.get())
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}", parent=self)


class GradeDialog(tk.Toplevel):
    def __init__(self, parent, db, grade=None, student_id=None):
        super().__init__(parent)
        self.db = db
        self.grade = grade
        self.preset_student_id = student_id
        self.result = None

        self.title("Редактировать оценку" if grade else "Добавить оценку")
        self.geometry("520x450")
        self.resizable(False, False)
        self.configure(bg='#f0f0f0')
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        if grade:
            self._fill_data()
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - self.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        # Студент
        ttk.Label(main_frame, text="Студент:*").grid(row=0, column=0, sticky='w', pady=5)
        self.students = self.db.get_all_students()
        student_names = [f"{s['last_name']} {s['first_name']} ({s['student_id']})" for s in self.students]
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(main_frame, textvariable=self.student_var, values=student_names, state='readonly')
        self.student_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)

        if self.preset_student_id:
            for i, s in enumerate(self.students):
                if s['id'] == self.preset_student_id:
                    self.student_combo.current(i)
                    break

        # Предмет
        ttk.Label(main_frame, text="Предмет:*").grid(row=1, column=0, sticky='w', pady=5)
        self.subjects = self.db.get_all_subjects()
        subject_names = [s['name'] for s in self.subjects]
        self.subject_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.subject_var, values=subject_names, state='readonly').grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Оценка
        ttk.Label(main_frame, text="Оценка:*").grid(row=2, column=0, sticky='w', pady=5)
        self.grade_var = tk.StringVar()
        grade_frame = ttk.Frame(main_frame)
        grade_frame.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        for val in [5, 4, 3, 2]:
            ttk.Radiobutton(grade_frame, text=str(val), variable=self.grade_var, value=str(val)).pack(side='left', padx=10)

        # Тип
        ttk.Label(main_frame, text="Тип:*").grid(row=3, column=0, sticky='w', pady=5)
        self.type_var = tk.StringVar(value="Экзамен")
        ttk.Combobox(main_frame, textvariable=self.type_var,
                     values=["Экзамен", "Зачёт", "Курсовая работа", "Контрольная работа", "Лабораторная"],
                     state='readonly').grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Дата
        ttk.Label(main_frame, text="Дата:*").grid(row=4, column=0, sticky='w', pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%d.%m.%Y'))
        ttk.Entry(main_frame, textvariable=self.date_var).grid(row=4, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Семестр
        ttk.Label(main_frame, text="Семестр:*").grid(row=5, column=0, sticky='w', pady=5)
        self.semester_var = tk.StringVar(value="1")
        ttk.Combobox(main_frame, textvariable=self.semester_var, values=[str(i) for i in range(1, 9)], state='readonly').grid(row=5, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Преподаватель
        ttk.Label(main_frame, text="Преподаватель:").grid(row=6, column=0, sticky='w', pady=5)
        self.teacher_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.teacher_var).grid(row=6, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0), sticky='e')

        ttk.Button(btn_frame, text="✗ Отмена", command=self.destroy).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✓ Сохранить", command=self._save).pack(side='left')

    def _fill_data(self):
        for i, s in enumerate(self.students):
            if s['id'] == self.grade['student_id']:
                self.student_combo.current(i)
                break
        for s in self.subjects:
            if s['id'] == self.grade['subject_id']:
                self.subject_var.set(s['name'])
                break
        self.grade_var.set(str(self.grade['grade']))
        self.type_var.set(self.grade['grade_type'])
        self.date_var.set(format_date(self.grade['date']))
        self.semester_var.set(str(self.grade['semester']))
        self.teacher_var.set(self.grade['teacher'] or '')

    def _save(self):
        s_idx = self.student_combo.current()
        sub_name = self.subject_var.get()
        grade_val = self.grade_var.get()
        date_str = self.date_var.get().strip()

        if s_idx < 0 or not sub_name or not grade_val or not date_str:
            messagebox.showerror("Ошибка", "Заполните обязательные поля!", parent=self)
            return

        date = parse_date(date_str)
        if not date:
            messagebox.showerror("Ошибка", "Формат даты: ДД.ММ.ГГГГ", parent=self)
            return

        student_id = self.students[s_idx]['id']
        subject_id = next((s['id'] for s in self.subjects if s['name'] == sub_name), None)

        try:
            if self.grade:
                self.db.update_grade(self.grade['id'], student_id, subject_id, int(grade_val), self.type_var.get(), date, int(self.semester_var.get()), self.teacher_var.get(), "")
            else:
                self.db.add_grade(student_id, subject_id, int(grade_val), self.type_var.get(), date, int(self.semester_var.get()), self.teacher_var.get(), "")
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}", parent=self)
