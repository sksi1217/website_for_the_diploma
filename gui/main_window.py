import tkinter as tk
from tkinter import ttk, messagebox
from gui.students_tab import StudentsTab
from gui.subjects_tab import SubjectsTab
from gui.grades_tab import GradesTab
from gui.reports_tab import ReportsTab
from gui.dialogs import GroupDialog
from datetime import datetime


class MainWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.title("АИС «Успеваемость студентов»")
        self.geometry("1200x700")
        self.minsize(1100, 700)
        self.configure(bg='#ecf0f1')

        self._apply_style()
        self._create_menu()
        self._create_header()
        self._create_notebook()
        self._create_statusbar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - self.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        style.configure('TNotebook', background='#ecf0f1')
        style.configure('TNotebook.Tab', padding=[12, 6], font=('Arial', 10))
        style.map('TNotebook.Tab',
                  background=[('selected', '#3498db'), ('active', '#5dade2')],
                  foreground=[('selected', 'white')])

        style.configure('TButton', padding=[8, 4], font=('Arial', 9))
        style.configure('TLabel', font=('Arial', 9))
        style.configure('TLabelframe.Label', font=('Arial', 9, 'bold'))

        style.configure('Treeview', font=('Arial', 9), rowheight=22)
        style.configure('Treeview.Heading', font=('Arial', 9, 'bold'))
        style.map('Treeview', background=[('selected', '#3498db')])

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.configure(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Управление группами", command=self._manage_groups)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close)

        # Данные
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Данные", menu=data_menu)
        data_menu.add_command(label="Загрузить демо-данные", command=self._load_demo)
        data_menu.add_command(label="Очистить все данные", command=self._clear_data)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._about)

    def _create_header(self):
        header = tk.Frame(self, bg='#2c3e50', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header,
                 text="🎓 АИС «Успеваемость студентов»",
                 bg='#2c3e50', fg='white',
                 font=('Arial', 16, 'bold')).pack(side='left', padx=20, pady=15)

        self.time_label = tk.Label(header, bg='#2c3e50', fg='#bdc3c7',
                                   font=('Arial', 10))
        self.time_label.pack(side='right', padx=20)
        self._update_time()

    def _update_time(self):
        now = datetime.now().strftime('%d.%m.%Y  %H:%M:%S')
        self.time_label.config(text=now)
        self.after(1000, self._update_time)

    def _create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        self.students_tab = StudentsTab(self.notebook, self.db)
        self.notebook.add(self.students_tab, text="👥 Студенты")

        self.subjects_tab = SubjectsTab(self.notebook, self.db)
        self.notebook.add(self.subjects_tab, text="📚 Предметы")

        self.grades_tab = GradesTab(self.notebook, self.db)
        self.notebook.add(self.grades_tab, text="📝 Оценки")

        self.reports_tab = ReportsTab(self.notebook, self.db)
        self.notebook.add(self.reports_tab, text="📊 Отчёты")

        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_change)

    def _create_statusbar(self):
        statusbar = tk.Frame(self, bg='#bdc3c7', height=25)
        statusbar.pack(fill='x', side='bottom')

        self.status_var = tk.StringVar(value="Готово")
        tk.Label(statusbar, textvariable=self.status_var,
                 bg='#bdc3c7', font=('Arial', 8)).pack(side='left', padx=10)

        # Статистика
        self.db_info_var = tk.StringVar()
        tk.Label(statusbar, textvariable=self.db_info_var,
                 bg='#bdc3c7', font=('Arial', 8)).pack(side='right', padx=10)
        self._update_db_info()

    def _update_db_info(self):
        try:
            students = len(self.db.get_all_students())
            subjects = len(self.db.get_all_subjects())
            grades = len(self.db.get_grades())
            self.db_info_var.set(f"Студентов: {students} | Предметов: {subjects} | Оценок: {grades}")
        except:
            pass
        self.after(5000, self._update_db_info)

    def _on_tab_change(self, event):
        tab = event.widget.tab(event.widget.select(), 'text')
        self.status_var.set(f"Раздел: {tab}")

    def _manage_groups(self):
        win = tk.Toplevel(self)
        win.title("Управление группами")
        win.geometry("600x400")
        win.transient(self)
        win.grab_set()

        toolbar = ttk.Frame(win)
        toolbar.pack(fill='x', padx=10, pady=5)
        ttk.Button(toolbar, text="➕ Добавить", command=lambda: self._add_group(win, tree)).pack(side='left', padx=2)
        ttk.Button(toolbar, text="✏️ Редактировать",
                   command=lambda: self._edit_group(win, tree)).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить",
                   command=lambda: self._delete_group(win, tree)).pack(side='left', padx=2)

        frame = ttk.Frame(win)
        frame.pack(fill='both', expand=True, padx=10, pady=5)

        tree = ttk.Treeview(frame, columns=('id', 'name', 'course', 'faculty'), show='headings')
        for col, text, width in [('id', 'ID', 40), ('name', 'Название', 120),
                                   ('course', 'Курс', 60), ('faculty', 'Факультет', 200)]:
            tree.heading(col, text=text)
            tree.column(col, width=width)

        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        def refresh_groups():
            tree.delete(*tree.get_children())
            for g in self.db.get_all_groups():
                tree.insert('', 'end', values=(g['id'], g['name'], g['course'], g['faculty']))

        refresh_groups()
        win._refresh = refresh_groups
        tree.bind('<Double-1>', lambda e: self._edit_group(win, tree))

    def _add_group(self, parent, tree):
        dlg = GroupDialog(parent, self.db)
        parent.wait_window(dlg)
        if dlg.result:
            parent._refresh()
            self.students_tab.refresh()

    def _edit_group(self, parent, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Предупреждение", "Выберите группу!", parent=parent)
            return
        gid = int(tree.item(sel[0])['values'][0])
        groups = self.db.get_all_groups()
        group = next((g for g in groups if g['id'] == gid), None)
        if group:
            dlg = GroupDialog(parent, self.db, group=group)
            parent.wait_window(dlg)
            if dlg.result:
                parent._refresh()
                self.students_tab.refresh()

    def _delete_group(self, parent, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Предупреждение", "Выберите группу!", parent=parent)
            return
        gid = int(tree.item(sel[0])['values'][0])
        if messagebox.askyesno("Подтверждение", "Удалить группу?", parent=parent):
            try:
                self.db.delete_group(gid)
                parent._refresh()
                self.students_tab.refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Нельзя удалить группу: {e}", parent=parent)

    def _load_demo(self):
        if not messagebox.askyesno("Демо-данные", "Загрузить тестовые данные?\nТекущие данные будут дополнены."):
            return

        try:
            # Группы (классы)
            g1 = self.db.add_group("5А", 5, "Начальная школа")
            g2 = self.db.add_group("7Б", 7, "Среднее звено")
            g3 = self.db.add_group("9В", 9, "Среднее звено")

            # Предметы
            s1 = self.db.add_subject("Математика", "Мат.", "Иванова С.П.", 136, 1, 5, "Урок")
            s2 = self.db.add_subject("Русский язык", "Рус.", "Петрова О.И.", 170, 1, 5, "Урок")
            s3 = self.db.add_subject("История", "Ист.", "Морозов В.А.", 68, 2, 7, "Урок")
            s4 = self.db.add_subject("Физика", "Физ.", "Козлов А.Б.", 68, 2, 9, "Урок")

            # Ученики
            from datetime import date
            students_data = [
                ("Иванов", "Артём", "Петрович", g1, "5А-001", "2014-05-15"),
                ("Петрова", "Мария", "Ивановна", g1, "5А-002", "2014-08-22"),
                ("Сидоров", "Дмитрий", "Алексеевич", g2, "7Б-001", "2012-12-10"),
                ("Козлова", "Анна", "Сергеевна", g2, "7Б-002", "2012-03-18"),
                ("Новиков", "Сергей", "Владимирович", g3, "9В-001", "2010-07-05"),
                ("Морозова", "Елена", "Николаевна", g3, "9В-002", "2010-01-30"),
            ]

            st_ids = []
            for ln, fn, mn, gid, sid, bd in students_data:
                st_id = self.db.add_student(ln, fn, mn, gid, sid, bd,
                    f"{ln.lower()}@school15.edu.ru", "")
                st_ids.append(st_id)

            # Оценки
            import random
            from datetime import datetime, timedelta
            subjects = [s1, s2, s3, s4]
            grade_types = ["Четверть", "Контрольная работа", "Самостоятельная работа"]
            grades_dist = [5, 5, 4, 4, 4, 3, 3, 2]

            for st_id in st_ids:
                for subj_id in random.sample(subjects, k=random.randint(2, 4)):
                    grade = random.choice(grades_dist)
                    date = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d')
                    self.db.add_grade(st_id, subj_id, grade,
                                      random.choice(grade_types), date,
                                      random.randint(1, 4), "Преподаватель", "")

            messagebox.showinfo("Успех", "Демо-данные успешно загружены!")
            self._refresh_all()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке: {e}")

    def _clear_data(self):
        if messagebox.askyesno("Очистка", "УДАЛИТЬ ВСЕ ДАННЫЕ?\nЭто действие необратимо!",
                               icon='warning'):
            if messagebox.askyesno("Подтверждение", "Вы уверены? Все данные будут потеряны!"):
                cursor = self.db.connection.cursor()
                for table in ['grades', 'attendance', 'students', 'subjects', 'groups']:
                    cursor.execute(f"DELETE FROM {table}")
                self.db.connection.commit()
                self._refresh_all()
                messagebox.showinfo("Готово", "Все данные удалены")

    def _refresh_all(self):
        self.students_tab.refresh()
        self.subjects_tab.refresh()
        self.grades_tab.refresh()

    def _about(self):
        messagebox.showinfo("О программе",
                            "АИС «Успеваемость студентов» v2.0\n\n"
                            "Автоматизированная информационная система\n"
                            "для учёта успеваемости студентов\n\n"
                            "Функции:\n"
                            "• Управление студентами и группами\n"
                            "• Учёт предметов и оценок\n"
                            "• Статистика и отчёты\n"
                            "• Экспорт данных в CSV\n\n"
                            "База данных: SQLite")

    def _on_close(self):
        if messagebox.askokcancel("Выход", "Выйти из программы?"):
            self.db.close()
            self.destroy()
