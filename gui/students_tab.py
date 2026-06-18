import tkinter as tk
from tkinter import ttk, messagebox
from gui.dialogs import StudentDialog
from utils import format_date, grade_color


class StudentsTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        # Панель инструментов
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=5)

        ttk.Button(toolbar, text="➕ Добавить", command=self._add).pack(side='left', padx=2)
        ttk.Button(toolbar, text="✏️ Редактировать", command=self._edit).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить", command=self._delete).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔄 Обновить", command=self.refresh).pack(side='left', padx=2)

        # Поиск и фильтры
        filter_frame = ttk.LabelFrame(self, text="Фильтры и поиск", padding=5)
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text="Поиск:").grid(row=0, column=0, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *a: self._on_search())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=25).grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Группа:").grid(row=0, column=2, padx=5)
        self.group_filter_var = tk.StringVar(value="Все")
        self.group_combo = ttk.Combobox(filter_frame, textvariable=self.group_filter_var,
                                         width=15, state='readonly')
        self.group_combo.grid(row=0, column=3, padx=5)
        self.group_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        ttk.Label(filter_frame, text="Статус:").grid(row=0, column=4, padx=5)
        self.status_filter_var = tk.StringVar(value="Все")
        ttk.Combobox(filter_frame, textvariable=self.status_filter_var,
                     values=["Все", "Активный", "Академический отпуск", "Отчислен", "Выпускник"],
                     width=18, state='readonly').grid(row=0, column=5, padx=5)
        self.status_filter_var.trace('w', lambda *a: self.refresh())

        # Таблица
        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('id', 'student_id', 'last_name', 'first_name', 'middle_name',
                   'group', 'birth_date', 'email', 'phone', 'status', 'avg_grade')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')

        headers = {
            'id': ('ID', 40), 'student_id': ('№ Зачётки', 90),
            'last_name': ('Фамилия', 120), 'first_name': ('Имя', 100),
            'middle_name': ('Отчество', 110), 'group': ('Группа', 80),
            'birth_date': ('Дата рожд.', 90), 'email': ('Email', 140),
            'phone': ('Телефон', 110), 'status': ('Статус', 110),
            'avg_grade': ('Ср. балл', 70)
        }

        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=width, minwidth=40)

        scroll_y = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side='right', fill='y')
        scroll_x.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<Double-1>', lambda e: self._edit())

        # Строка состояния
        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief='sunken').pack(fill='x', padx=10, pady=2)

        self._sort_col = None
        self._sort_rev = False

    def _update_group_filter(self):
        groups = self.db.get_all_groups()
        group_names = ["Все"] + [g['name'] for g in groups]
        self.group_combo['values'] = group_names
        if self.group_filter_var.get() not in group_names:
            self.group_filter_var.set("Все")

    def refresh(self):
        self._update_group_filter()
        search = self.search_var.get().strip()
        group_name = self.group_filter_var.get()
        status = self.status_filter_var.get()

        if search:
            students = self.db.search_students(search)
        else:
            group_id = None
            if group_name != "Все":
                groups = self.db.get_all_groups()
                for g in groups:
                    if g['name'] == group_name:
                        group_id = g['id']
                        break

            status_filter = None if status == "Все" else status
            students = self.db.get_all_students(group_id=group_id, status=status_filter)

        self.tree.delete(*self.tree.get_children())
        for s in students:
            avg = self.db.get_student_average(s['id'])
            avg_str = f"{avg:.2f}" if avg else "—"
            birth = format_date(s['birth_date']) if s['birth_date'] else ''

            tag = ''
            if s['status'] == 'Отчислен':
                tag = 'expelled'
            elif s['status'] == 'Академический отпуск':
                tag = 'leave'

            self.tree.insert('', 'end', values=(
                s['id'], s['student_id'], s['last_name'], s['first_name'],
                s['middle_name'] or '', s['group_name'], birth,
                s['email'] or '', s['phone'] or '', s['status'], avg_str
            ), tags=(tag,))

        self.tree.tag_configure('expelled', foreground='#e74c3c')
        self.tree.tag_configure('leave', foreground='#f39c12')

        self.status_var.set(f"Студентов: {len(students)}")

    def _on_search(self):
        self.refresh()

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def _add(self):
        dlg = StudentDialog(self.winfo_toplevel(), self.db)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()

    def _edit(self):
        sid = self._get_selected_id()
        if not sid:
            messagebox.showwarning("Предупреждение", "Выберите студента!")
            return
        student = self.db.get_student_by_id(sid)
        dlg = StudentDialog(self.winfo_toplevel(), self.db, student=student)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()

    def _delete(self):
        sid = self._get_selected_id()
        if not sid:
            messagebox.showwarning("Предупреждение", "Выберите студента!")
            return
        student = self.db.get_student_by_id(sid)
        name = f"{student['last_name']} {student['first_name']}"
        if messagebox.askyesno("Подтверждение", f"Удалить студента '{name}'?\nВсе его оценки будут удалены!"):
            self.db.delete_student(sid)
            self.refresh()

    def _sort(self, col):
        data = [(self.tree.set(c, col), c) for c in self.tree.get_children('')]
        reverse = self._sort_rev if self._sort_col == col else False
        try:
            data.sort(key=lambda x: float(x[0]) if x[0] not in ('', '—') else -1, reverse=reverse)
        except ValueError:
            data.sort(key=lambda x: x[0].lower(), reverse=reverse)
        for idx, (_, item) in enumerate(data):
            self.tree.move(item, '', idx)
        self._sort_col = col
        self._sort_rev = not reverse
