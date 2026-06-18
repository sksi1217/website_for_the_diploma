import tkinter as tk
from tkinter import ttk, messagebox
from gui.dialogs import SubjectDialog


class SubjectsTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=5)

        ttk.Button(toolbar, text="➕ Добавить", command=self._add).pack(side='left', padx=2)
        ttk.Button(toolbar, text="✏️ Редактировать", command=self._edit).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить", command=self._delete).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔄 Обновить", command=self.refresh).pack(side='left', padx=2)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('id', 'name', 'short_name', 'teacher', 'hours', 'semester', 'course', 'type')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        headers = {
            'id': ('ID', 40), 'name': ('Название', 200), 'short_name': ('Аббр.', 80),
            'teacher': ('Преподаватель', 160), 'hours': ('Часы', 60),
            'semester': ('Семестр', 70), 'course': ('Курс', 60), 'type': ('Тип', 100)
        }
        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)

        scroll_y = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<Double-1>', lambda e: self._edit())

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief='sunken').pack(fill='x', padx=10, pady=2)

    def refresh(self):
        subjects = self.db.get_all_subjects()
        self.tree.delete(*self.tree.get_children())
        for s in subjects:
            self.tree.insert('', 'end', values=(
                s['id'], s['name'], s['short_name'] or '',
                s['teacher'] or '', s['hours'] or 0,
                s['semester'], s['course'], s['subject_type']
            ))
        self.status_var.set(f"Предметов: {len(subjects)}")

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def _add(self):
        dlg = SubjectDialog(self.winfo_toplevel(), self.db)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()

    def _edit(self):
        sid = self._get_selected_id()
        if not sid:
            messagebox.showwarning("Предупреждение", "Выберите предмет!")
            return
        subjects = self.db.get_all_subjects()
        subject = next((s for s in subjects if s['id'] == sid), None)
        if subject:
            dlg = SubjectDialog(self.winfo_toplevel(), self.db, subject=subject)
            self.wait_window(dlg)
            if dlg.result:
                self.refresh()

    def _delete(self):
        sid = self._get_selected_id()
        if not sid:
            messagebox.showwarning("Предупреждение", "Выберите предмет!")
            return
        if messagebox.askyesno("Подтверждение", "Удалить предмет? Все связанные оценки будут удалены!"):
            self.db.delete_subject(sid)
            self.refresh()
