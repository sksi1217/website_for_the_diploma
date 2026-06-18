import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime


class ReportsTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self._create_widgets()

    def _create_widgets(self):
        # Левая панель — выбор отчёта
        left_frame = ttk.LabelFrame(self, text="Тип отчёта", padding=10)
        left_frame.pack(side='left', fill='y', padx=10, pady=10)

        self.report_var = tk.StringVar(value="group_stat")
        reports = [
            ("group_stat", "📊 Успеваемость группы"),
            ("subject_stat", "📚 Статистика по предметам"),
            ("excellent", "🌟 Список отличников"),
            ("failing", "⚠️ Должники"),
            ("distribution", "📈 Распределение оценок"),
            ("student_card", "👤 Карточка студента"),
        ]

        for value, text in reports:
            ttk.Radiobutton(left_frame, text=text, variable=self.report_var,
                           value=value, command=self._update_params).pack(anchor='w', pady=3)

        # Параметры
        self.params_frame = ttk.LabelFrame(left_frame, text="Параметры", padding=10)
        self.params_frame.pack(fill='x', pady=10)

        ttk.Button(left_frame, text="▶ Сформировать отчёт",
                   command=self._generate).pack(fill='x', pady=5)
        ttk.Button(left_frame, text="💾 Экспорт в CSV",
                   command=self._export_csv).pack(fill='x', pady=2)

        # Правая панель — результаты
        right_frame = ttk.Frame(self)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        self.result_tree = ttk.Treeview(right_frame, show='headings')
        scroll_y = ttk.Scrollbar(right_frame, orient='vertical', command=self.result_tree.yview)
        scroll_x = ttk.Scrollbar(right_frame, orient='horizontal', command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_x.pack(side='bottom', fill='x')
        scroll_y.pack(side='right', fill='y')
        self.result_tree.pack(fill='both', expand=True)

        self.info_var = tk.StringVar()
        ttk.Label(right_frame, textvariable=self.info_var,
                  font=('Arial', 10, 'bold')).pack(pady=5)

        self._update_params()
        self._generate()

    def _update_params(self):
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        report = self.report_var.get()

        if report in ("group_stat", "excellent", "failing"):
            ttk.Label(self.params_frame, text="Группа:").pack(anchor='w')
            self.param_group_var = tk.StringVar(value="Все")
            groups = self.db.get_all_groups()
            group_names = ["Все"] + [g['name'] for g in groups]
            self._groups_list = groups
            ttk.Combobox(self.params_frame, textvariable=self.param_group_var,
                        values=group_names, state='readonly').pack(fill='x', pady=3)

        if report == "group_stat":
            ttk.Label(self.params_frame, text="Семестр:").pack(anchor='w')
            self.param_semester_var = tk.StringVar(value="Все")
            ttk.Combobox(self.params_frame, textvariable=self.param_semester_var,
                        values=["Все", "1", "2", "3", "4", "5", "6", "7", "8"],
                        state='readonly').pack(fill='x', pady=3)

        if report == "student_card":
            ttk.Label(self.params_frame, text="Студент:").pack(anchor='w')
            self.param_student_var = tk.StringVar()
            students = self.db.get_all_students()
            self._students_list = students
            student_names = [
                f"{s['last_name']} {s['first_name']} ({s['student_id']})"
                for s in students
            ]
            ttk.Combobox(self.params_frame, textvariable=self.param_student_var,
                        values=student_names, state='readonly').pack(fill='x', pady=3)
            if students:
                self.param_student_var.set(student_names[0])

    def _generate(self):
        report = self.report_var.get()

        if report == "group_stat":
            self._report_group_stat()
        elif report == "subject_stat":
            self._report_subject_stat()
        elif report == "excellent":
            self._report_excellent()
        elif report == "failing":
            self._report_failing()
        elif report == "distribution":
            self._report_distribution()
        elif report == "student_card":
            self._report_student_card()

    def _setup_tree(self, columns, headers, widths):
        self.result_tree.delete(*self.result_tree.get_children())
        self.result_tree['columns'] = columns
        for col, head, width in zip(columns, headers, widths):
            self.result_tree.heading(col, text=head)
            self.result_tree.column(col, width=width, minwidth=50)

    def _report_group_stat(self):
        group_id = None
        if hasattr(self, 'param_group_var') and self.param_group_var.get() != "Все":
            gname = self.param_group_var.get()
            for g in self._groups_list:
                if g['name'] == gname:
                    group_id = g['id']
                    break

        if not group_id:
            groups = self.db.get_all_groups()
            if not groups:
                messagebox.showinfo("Информация", "Нет групп в базе данных")
                return

        semester = None
        if hasattr(self, 'param_semester_var') and self.param_semester_var.get() != "Все":
            semester = int(self.param_semester_var.get())

        data = self.db.get_group_statistics(group_id, semester)

        if group_id:
            cols = ('name', 'student_number', 'count', 'avg', '5', '4', '3', '2')
            heads = ['ФИО', '№ Зачётки', 'Оценок', 'Ср. балл', '5', '4', '3', '2']
            widths = [200, 90, 60, 80, 40, 40, 40, 40]
        else:
            cols = ('name', 'group', 'student_number', 'count', 'avg', '5', '4', '3', '2')
            heads = ['ФИО', 'Класс', '№ Зачётки', 'Оценок', 'Ср. балл', '5', '4', '3', '2']
            widths = [180, 60, 90, 60, 80, 40, 40, 40, 40]
        self._setup_tree(cols, heads, widths)

        total_avg = 0
        count = 0
        for row in data:
            name = f"{row['last_name']} {row['first_name']} {row['middle_name'] or ''}".strip()
            avg = round(row['avg_grade'], 2) if row['avg_grade'] else 0
            total_avg += avg
            count += 1

            tag = 'excellent' if avg >= 4.5 else ('failing' if (row['twos'] or 0) > 0 else '')
            values = (
                name,
                *([] if group_id else [row['group_name']]),
                row['student_number'], row['grades_count'] or 0,
                f"{avg:.2f}" if avg else "—",
                row['fives'] or 0, row['fours'] or 0,
                row['threes'] or 0, row['twos'] or 0
            )
            self.result_tree.insert('', 'end', values=values, tags=(tag,))

        self.result_tree.tag_configure('excellent', foreground='#27ae60')
        self.result_tree.tag_configure('failing', foreground='#e74c3c')

        avg_total = total_avg / count if count else 0
        if group_id:
            self.info_var.set(f"Студентов: {count} | Средний балл группы: {avg_total:.2f}")
        else:
            groups_count = len({row['group_name'] for row in data})
            self.info_var.set(f"Все классы ({groups_count}) | Студентов: {count} | Средний балл: {avg_total:.2f}")

    def _report_subject_stat(self):
        data = self.db.get_subject_statistics()
        cols = ('subject', 'total', 'avg', '5', '4', '3', '2')
        heads = ['Предмет', 'Оценок', 'Ср. балл', '5', '4', '3', '2']
        widths = [220, 70, 80, 50, 50, 50, 50]
        self._setup_tree(cols, heads, widths)

        for row in data:
            avg = round(row['avg_grade'], 2) if row['avg_grade'] else 0
            self.result_tree.insert('', 'end', values=(
                row['subject_name'], row['total_grades'] or 0,
                f"{avg:.2f}" if avg else "—",
                row['fives'] or 0, row['fours'] or 0,
                row['threes'] or 0, row['twos'] or 0
            ))

        self.info_var.set(f"Предметов: {len(data)}")

    def _report_excellent(self):
        group_id = None
        if hasattr(self, 'param_group_var') and self.param_group_var.get() != "Все":
            gname = self.param_group_var.get()
            for g in self._groups_list:
                if g['name'] == gname:
                    group_id = g['id']
                    break

        data = self.db.get_excellent_students(group_id)
        cols = ('name', 'student_number', 'group', 'avg', 'count')
        heads = ['ФИО', '№ Зачётки', 'Группа', 'Ср. балл', 'Оценок']
        widths = [200, 90, 80, 80, 60]
        self._setup_tree(cols, heads, widths)

        for row in data:
            name = f"{row['last_name']} {row['first_name']} {row['middle_name'] or ''}".strip()
            self.result_tree.insert('', 'end', values=(
                name, row['student_number'], row['group_name'],
                f"{row['avg_grade']:.2f}", row['grades_count']
            ), tags=('excellent',))

        self.result_tree.tag_configure('excellent', foreground='#27ae60', font=('Arial', 9, 'bold'))
        self.info_var.set(f"Отличников: {len(data)}")

    def _report_failing(self):
        group_id = None
        if hasattr(self, 'param_group_var') and self.param_group_var.get() != "Все":
            gname = self.param_group_var.get()
            for g in self._groups_list:
                if g['name'] == gname:
                    group_id = g['id']
                    break

        data = self.db.get_failing_students(group_id)
        cols = ('name', 'student_number', 'group', 'debts')
        heads = ['ФИО', '№ Зачётки', 'Группа', 'Долгов']
        widths = [200, 90, 80, 60]
        self._setup_tree(cols, heads, widths)

        for row in data:
            name = f"{row['last_name']} {row['first_name']} {row['middle_name'] or ''}".strip()
            self.result_tree.insert('', 'end', values=(
                name, row['student_number'], row['group_name'], row['debt_count']
            ), tags=('failing',))

        self.result_tree.tag_configure('failing', foreground='#e74c3c', font=('Arial', 9, 'bold'))
        self.info_var.set(f"Студентов с долгами: {len(data)}")

    def _report_distribution(self):
        data = self.db.get_grade_distribution()
        cols = ('grade', 'label', 'count', 'percent')
        heads = ['Оценка', 'Словесно', 'Количество', 'Процент']
        widths = [70, 160, 100, 80]
        self._setup_tree(cols, heads, widths)

        labels = {5: 'Отлично', 4: 'Хорошо', 3: 'Удовл.', 2: 'Неудовл.'}
        colors = {5: '#27ae60', 4: '#2980b9', 3: '#e67e22', 2: '#e74c3c'}
        total = sum(r['count'] for r in data)

        for row in data:
            pct = round(row['count'] / total * 100, 1) if total else 0
            grade = row['grade']
            self.result_tree.insert('', 'end', values=(
                grade, labels.get(grade, ''), row['count'], f"{pct}%"
            ), tags=(f'g{grade}',))
            self.result_tree.tag_configure(f'g{grade}', foreground=colors.get(grade, 'black'))

        self.info_var.set(f"Всего оценок: {total}")

    def _report_student_card(self):
        if not hasattr(self, 'param_student_var') or not hasattr(self, '_students_list'):
            return

        student_str = self.param_student_var.get()
        student_id = None
        for s in self._students_list:
            if f"{s['last_name']} {s['first_name']} ({s['student_id']})" == student_str:
                student_id = s['id']
                break

        if not student_id:
            return

        grades = self.db.get_grades(student_id=student_id)
        cols = ('subject', 'grade', 'type', 'date', 'semester', 'teacher')
        heads = ['Предмет', 'Оценка', 'Тип', 'Дата', 'Семестр', 'Преподаватель']
        widths = [200, 60, 120, 90, 70, 160]
        self._setup_tree(cols, heads, widths)

        grade_labels = {5: '5 — Отлично', 4: '4 — Хорошо',
                        3: '3 — Удовл.', 2: '2 — Неудовл.'}
        grade_colors = {5: '#27ae60', 4: '#2980b9', 3: '#e67e22', 2: '#e74c3c'}

        for g in grades:
            grade_val = g['grade']
            self.result_tree.insert('', 'end', values=(
                g['subject_name'],
                grade_labels.get(grade_val, str(grade_val)),
                g['grade_type'],
                g['date'],
                g['semester'],
                g['teacher'] or ''
            ), tags=(f'g{grade_val}',))
            self.result_tree.tag_configure(f'g{grade_val}',
                                           foreground=grade_colors.get(grade_val, 'black'))

        avg = self.db.get_student_average(student_id)
        self.info_var.set(f"Оценок: {len(grades)} | Средний балл: {avg:.2f}")

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='', encoding='cp1251') as f:
                f.write('sep=;\n')
                writer = csv.writer(f, delimiter=';')
                cols = self.result_tree['columns']
                headers = [self.result_tree.heading(c)['text'] for c in cols]
                writer.writerow(headers)
                for item in self.result_tree.get_children():
                    writer.writerow(self.result_tree.item(item)['values'])
            messagebox.showinfo("Успех", f"Файл сохранён:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")
