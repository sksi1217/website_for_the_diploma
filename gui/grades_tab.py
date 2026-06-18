import tkinter as tk
from tkinter import ttk, messagebox
from gui.dialogs import GradeDialog
from utils import format_date, grade_color


class GradesTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=5)

        ttk.Button(toolbar, text="➕ Добавить оценку", command=self._add).pack(side='left', padx=2)
        ttk.Button(toolbar, text="✏️ Редактировать", command=self._edit).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить", command=self._delete).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔄 Обновить", command=self.refresh).pack(side='left', padx=2)

        filter_frame = ttk.LabelFrame(self, text="Фильтры", padding=5)
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text="Студент:").grid(row=0, column=0, padx=5)
        self.student_filter_var = tk.StringVar(value="Все")
        self.student_combo = ttk.Combobox(filter_frame, textvariable=self.student_filter_var,
                                           width=30, state='readonly')
        self.student_combo.grid(row=0, column=1, padx=5)
        self.student_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        ttk.Label(filter_frame, text="Предмет:").grid(row=0, column=2, padx=5)
        self.subject_filter_var = tk.StringVar(value="Все")
        self.subject_combo = ttk.Combobox(filter_frame, textvariable=self.subject_filter_var,
                                           width=25, state='readonly')
        self.subject_combo.grid(row=0, column=3, padx=5)
        self.subject_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        ttk.Label(filter_frame, text="Семестр:").grid(row=0, column=4, padx=5)
        self.semester_filter_var = tk.StringVar(value="Все")
        ttk.Combobox(filter_frame, textvariable=self.semester_filter_var,
                     values=["Все", "1", "2", "3", "4", "5", "6", "7", "8"],
                     width=8, state='readonly').grid(row=0, column=5, padx=5)
        self.semester_filter_var.trace('w', lambda *a: self.refresh())

        # Таблица
        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('id', 'student', 'group', 'subject', 'grade', 'type', 'date', 'semester', 'teacher')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        headers = {
            'id': ('ID', 40), 'student': ('Студент', 180), 'group': ('Группа', 80),
            'subject': ('Предмет', 160), 'grade': ('Оценка', 60), 'type': ('Тип', 120),
            'date': ('Дата', 90), 'semester': ('Сем.', 50), 'teacher': ('Преподаватель', 150)
        }
        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)

        scroll_y = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side='right', fill='y')
        scroll_x.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure('grade_5', foreground='#27ae60')
        self.tree.tag_configure('grade_4', foreground='#2980b9')
        self.tree.tag_configure('grade_3', foreground='#e67e22')
        self.tree.tag_configure('grade_2', foreground='#e74c3c', font=('Arial', 9, 'bold'))

        self.tree.bind('<Double-1>', lambda e: self._edit())

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief='sunken').pack(fill='x', padx=10, pady=2)

    def _update_filters(self):
        students = self.db.get_all_students()
        student_names = ["Все"] + [
            f"{s['last_name']} {s['first_name']} ({s['student_id']})"
            for s in students
        ]
        current_s = self.student_filter_var.get()
        self.student_combo['values'] = student_names
        if current_s not in student_names:
            self.student_filter_var.set("Все")
        self._students_list = students

        subjects = self.db.get_all_subjects()
        subject_names = ["Все"] + [s['name'] for s in subjects]
        current_sub = self.subject_filter_var.get()
        self.subject_combo['values'] = subject_names
        if current_sub not in subject_names:
            self.subject_filter_var.set("Все")
        self._subjects_list = subjects

    def refresh(self):
        self._update_filters()

        student_id = None
        student_str = self.student_filter_var.get()
        if student_str != "Все" and hasattr(self, '_students_list'):
            for s in self._students_list:
                if f"{s['last_name']} {s['first_name']} ({s['student_id']})" == student_str:
                    student_id = s['id']
                    break

        subject_id = None
        subject_str = self.subject_filter_var.get()
        if subject_str != "Все" and hasattr(self, '_subjects_list'):
            for s in self._subjects_list:
                if s['name'] == subject_str:
                    subject_id = s['id']
                    break

        semester = None
        sem_str = self.semester_filter_var.get()
        if sem_str != "Все":
            semester = int(sem_str)

        grades = self.db.get_grades(student_id=student_id, subject_id=subject_id, semester=semester)

        self.tree.delete(*self.tree.get_children())
        grade_labels = {5: '5 — Отлично', 4: '4 — Хорошо',
                        3: '3 — Удовл.', 2: '2 — Неудовл.'}

        for g in grades:
            grade_val = g['grade']
            tag = f'grade_{grade_val}'
            self.tree.insert('', 'end', values=(
                g['id'],
                g['student_name'].strip(),
                g['group_name'],
                g['subject_name'],
                grade_labels.get(grade_val, str(grade_val)),
                g['grade_type'],
                format_date(g['date']),
                g['semester'],
                g['teacher'] or ''
            ), tags=(tag,))

        self.status_var.set(f"Записей: {len(grades)}")

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def _add(self):
        dlg = GradeDialog(self.winfo_toplevel(), self.db)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()

    def _edit(self):
        gid = self._get_selected_id()
        if not gid:
            messagebox.showwarning("Предупреждение", "Выберите запись!")
            return
        grades = self.db.get_grades()
        grade = next((g for g in grades if g['id'] == gid), None)
        if grade:
            dlg = GradeDialog(self.winfo_toplevel(), self.db, grade=grade)
            self.wait_window(dlg)
            if dlg.result:
                self.refresh()

    def _delete(self):
        gid = self._get_selected_id()
        if not gid:
            messagebox.showwarning("Предупреждение", "Выберите запись!")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранную оценку?"):
            self.db.delete_grade(gid)
            self.refresh()
