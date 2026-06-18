import sqlite3
import os
from datetime import datetime


class Database:
    def __init__(self, db_path="student_performance.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Подключение к базе данных"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")

    def create_tables(self):
        """Создание таблиц базы данных"""
        cursor = self.connection.cursor()

        # Таблица групп
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                course INTEGER NOT NULL,
                faculty TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Таблица студентов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                group_id INTEGER NOT NULL,
                student_id TEXT UNIQUE NOT NULL,
                birth_date TEXT,
                email TEXT,
                phone TEXT,
                status TEXT DEFAULT 'Активный',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE RESTRICT
            )
        """)

        # Таблица предметов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                short_name TEXT,
                teacher TEXT,
                hours INTEGER DEFAULT 0,
                semester INTEGER,
                course INTEGER,
                subject_type TEXT DEFAULT 'Лекция',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Таблица оценок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                grade INTEGER NOT NULL CHECK(grade >= 2 AND grade <= 5),
                grade_type TEXT NOT NULL,
                date TEXT NOT NULL,
                semester INTEGER NOT NULL,
                teacher TEXT,
                comment TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        """)

        # Таблица посещаемости
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Присутствовал',
                reason TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        """)

        self.connection.commit()

    def close(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()

    # ==================== ГРУППЫ ====================

    def get_all_groups(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM groups ORDER BY course, name")
        return cursor.fetchall()

    def add_group(self, name, course, faculty):
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO groups (name, course, faculty) VALUES (?, ?, ?)",
            (name, course, faculty)
        )
        self.connection.commit()
        return cursor.lastrowid

    def update_group(self, group_id, name, course, faculty):
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE groups SET name=?, course=?, faculty=? WHERE id=?",
            (name, course, faculty, group_id)
        )
        self.connection.commit()

    def delete_group(self, group_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM groups WHERE id=?", (group_id,))
        self.connection.commit()

    # ==================== СТУДЕНТЫ ====================

    def get_all_students(self, group_id=None, status=None):
        cursor = self.connection.cursor()
        query = """
            SELECT s.*, g.name as group_name, g.course, g.faculty
            FROM students s
            JOIN groups g ON s.group_id = g.id
            WHERE 1=1
        """
        params = []
        if group_id:
            query += " AND s.group_id = ?"
            params.append(group_id)
        if status:
            query += " AND s.status = ?"
            params.append(status)
        query += " ORDER BY s.last_name, s.first_name"
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_student_by_id(self, student_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT s.*, g.name as group_name
            FROM students s
            JOIN groups g ON s.group_id = g.id
            WHERE s.id = ?
        """, (student_id,))
        return cursor.fetchone()

    def search_students(self, query):
        cursor = self.connection.cursor()
        search = f"%{query}%"
        cursor.execute("""
            SELECT s.*, g.name as group_name
            FROM students s
            JOIN groups g ON s.group_id = g.id
            WHERE s.last_name LIKE ? OR s.first_name LIKE ?
                OR s.middle_name LIKE ? OR s.student_id LIKE ?
            ORDER BY s.last_name, s.first_name
        """, (search, search, search, search))
        return cursor.fetchall()

    def add_student(self, last_name, first_name, middle_name, group_id,
                    student_id, birth_date, email, phone, status='Активный'):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO students
            (last_name, first_name, middle_name, group_id, student_id,
             birth_date, email, phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (last_name, first_name, middle_name, group_id, student_id,
              birth_date, email, phone, status))
        self.connection.commit()
        return cursor.lastrowid

    def update_student(self, sid, last_name, first_name, middle_name, group_id,
                       student_id, birth_date, email, phone, status):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE students SET last_name=?, first_name=?, middle_name=?,
            group_id=?, student_id=?, birth_date=?, email=?, phone=?, status=?
            WHERE id=?
        """, (last_name, first_name, middle_name, group_id, student_id,
              birth_date, email, phone, status, sid))
        self.connection.commit()

    def delete_student(self, student_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
        self.connection.commit()

    # ==================== ПРЕДМЕТЫ ====================

    def get_all_subjects(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM subjects ORDER BY course, semester, name")
        return cursor.fetchall()

    def add_subject(self, name, short_name, teacher, hours, semester, course, subject_type):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO subjects (name, short_name, teacher, hours, semester, course, subject_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, short_name, teacher, hours, semester, course, subject_type))
        self.connection.commit()
        return cursor.lastrowid

    def update_subject(self, sid, name, short_name, teacher, hours, semester, course, subject_type):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE subjects SET name=?, short_name=?, teacher=?, hours=?,
            semester=?, course=?, subject_type=? WHERE id=?
        """, (name, short_name, teacher, hours, semester, course, subject_type, sid))
        self.connection.commit()

    def delete_subject(self, subject_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
        self.connection.commit()

    def clear_all_data(self):
        """Полная очистка данных и сброс счётчиков ID с 1."""
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        for table in ["grades", "attendance", "students", "subjects", "groups"]:
            cursor.execute(f"DELETE FROM {table}")
        cursor.execute("DELETE FROM sqlite_sequence")
        cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()
        cursor.execute("VACUUM")

    def count_grades(self, student_id=None, subject_id=None, semester=None):
        cursor = self.connection.cursor()
        query = "SELECT COUNT(*) FROM grades g WHERE 1=1"
        params = []
        if student_id:
            query += " AND g.student_id = ?"
            params.append(student_id)
        if subject_id:
            query += " AND g.subject_id = ?"
            params.append(subject_id)
        if semester:
            query += " AND g.semester = ?"
            params.append(semester)
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    # ==================== ОЦЕНКИ ====================

    def get_grades(self, student_id=None, subject_id=None, semester=None, limit=None):
        cursor = self.connection.cursor()
        query = """
            SELECT g.*,
                   s.last_name || ' ' || s.first_name || ' ' || COALESCE(s.middle_name,'') as student_name,
                   s.student_id as student_number,
                   sub.name as subject_name,
                   gr.name as group_name
            FROM grades g
            JOIN students s ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN groups gr ON s.group_id = gr.id
            WHERE 1=1
        """
        params = []
        if student_id:
            query += " AND g.student_id = ?"
            params.append(student_id)
        if subject_id:
            query += " AND g.subject_id = ?"
            params.append(subject_id)
        if semester:
            query += " AND g.semester = ?"
            params.append(semester)
        query += " ORDER BY g.date DESC, g.id DESC"
        if limit:
            query += " LIMIT ?"
            params.append(int(limit))
        cursor.execute(query, params)
        return cursor.fetchall()

    def add_grades_bulk(self, rows):
        """Пакетная вставка оценок (один commit)."""
        if not rows:
            return
        cursor = self.connection.cursor()
        cursor.executemany("""
            INSERT INTO grades (student_id, subject_id, grade, grade_type, date, semester, teacher, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        self.connection.commit()

    def get_grade_by_id(self, grade_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT g.*,
                   s.last_name || ' ' || s.first_name || ' ' || COALESCE(s.middle_name,'') as student_name,
                   s.student_id as student_number,
                   sub.name as subject_name,
                   gr.name as group_name
            FROM grades g
            JOIN students s ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN groups gr ON s.group_id = gr.id
            WHERE g.id = ?
        """, (grade_id,))
        return cursor.fetchone()

    def add_grade(self, student_id, subject_id, grade, grade_type, date, semester, teacher, comment):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO grades (student_id, subject_id, grade, grade_type, date, semester, teacher, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, subject_id, grade, grade_type, date, semester, teacher, comment))
        self.connection.commit()
        return cursor.lastrowid

    def update_grade(self, gid, student_id, subject_id, grade, grade_type, date, semester, teacher, comment):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE grades SET student_id=?, subject_id=?, grade=?, grade_type=?,
            date=?, semester=?, teacher=?, comment=? WHERE id=?
        """, (student_id, subject_id, grade, grade_type, date, semester, teacher, comment, gid))
        self.connection.commit()

    def delete_grade(self, grade_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM grades WHERE id=?", (grade_id,))
        self.connection.commit()

    # ==================== СТАТИСТИКА ====================

    def get_student_average(self, student_id, semester=None):
        cursor = self.connection.cursor()
        query = "SELECT AVG(grade) FROM grades WHERE student_id=?"
        params = [student_id]
        if semester:
            query += " AND semester=?"
            params.append(semester)
        cursor.execute(query, params)
        result = cursor.fetchone()[0]
        return round(result, 2) if result else 0

    def get_student_averages_map(self):
        """Средние баллы всех учеников одним запросом."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT student_id, ROUND(AVG(grade), 2) as avg_grade
            FROM grades
            GROUP BY student_id
        """)
        return {row["student_id"]: row["avg_grade"] for row in cursor.fetchall()}

    def get_stats(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM students) as students,
                (SELECT COUNT(*) FROM subjects) as subjects,
                (SELECT COUNT(*) FROM grades) as grades
        """)
        return dict(cursor.fetchone())

    def get_students_options(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, last_name, first_name, student_id
            FROM students
            ORDER BY last_name, first_name
        """)
        return cursor.fetchall()

    def get_group_statistics(self, group_id=None, semester=None):
        cursor = self.connection.cursor()
        query = """
            SELECT
                s.id, s.last_name, s.first_name, s.middle_name,
                s.student_id as student_number,
                gr.name as group_name,
                COUNT(g.id) as grades_count,
                AVG(g.grade) as avg_grade,
                SUM(CASE WHEN g.grade = 5 THEN 1 ELSE 0 END) as fives,
                SUM(CASE WHEN g.grade = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN g.grade = 3 THEN 1 ELSE 0 END) as threes,
                SUM(CASE WHEN g.grade = 2 THEN 1 ELSE 0 END) as twos
            FROM students s
            JOIN groups gr ON s.group_id = gr.id
            LEFT JOIN grades g ON s.id = g.student_id
            WHERE 1=1
        """
        params = []
        if group_id:
            query += " AND s.group_id = ?"
            params.append(group_id)
        if semester:
            query += " AND (g.semester=? OR g.semester IS NULL)"
            params.append(semester)
        query += " GROUP BY s.id ORDER BY gr.name, s.last_name, s.first_name"
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_subject_statistics(self, subject_id=None):
        cursor = self.connection.cursor()
        query = """
            SELECT
                sub.name as subject_name,
                COUNT(g.id) as total_grades,
                AVG(g.grade) as avg_grade,
                SUM(CASE WHEN g.grade = 5 THEN 1 ELSE 0 END) as fives,
                SUM(CASE WHEN g.grade = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN g.grade = 3 THEN 1 ELSE 0 END) as threes,
                SUM(CASE WHEN g.grade = 2 THEN 1 ELSE 0 END) as twos
            FROM subjects sub
            LEFT JOIN grades g ON sub.id = g.subject_id
        """
        params = []
        if subject_id:
            query += " WHERE sub.id=?"
            params.append(subject_id)
        query += " GROUP BY sub.id ORDER BY sub.name"
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_grade_distribution(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT grade, COUNT(*) as count
            FROM grades
            GROUP BY grade
            ORDER BY grade
        """)
        return cursor.fetchall()

    def get_excellent_students(self, group_id=None):
        """Отличники (средний балл >= 4.5)"""
        cursor = self.connection.cursor()
        query = """
            SELECT s.last_name, s.first_name, s.middle_name,
                   s.student_id as student_number,
                   g.name as group_name,
                   AVG(gr.grade) as avg_grade,
                   COUNT(gr.id) as grades_count
            FROM students s
            JOIN groups g ON s.group_id = g.id
            LEFT JOIN grades gr ON s.id = gr.student_id
            WHERE s.status = 'Активный'
        """
        params = []
        if group_id:
            query += " AND s.group_id=?"
            params.append(group_id)
        query += """
            GROUP BY s.id
            HAVING AVG(gr.grade) >= 4.5
            ORDER BY avg_grade DESC, s.last_name
        """
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_failing_students(self, group_id=None):
        """Должники (есть оценка 2)"""
        cursor = self.connection.cursor()
        query = """
            SELECT DISTINCT s.last_name, s.first_name, s.middle_name,
                   s.student_id as student_number,
                   g.name as group_name,
                   COUNT(gr.id) as debt_count
            FROM students s
            JOIN groups g ON s.group_id = g.id
            JOIN grades gr ON s.id = gr.student_id
            WHERE gr.grade = 2 AND s.status = 'Активный'
        """
        params = []
        if group_id:
            query += " AND s.group_id=?"
            params.append(group_id)
        query += " GROUP BY s.id ORDER BY debt_count DESC, s.last_name"
        cursor.execute(query, params)
        return cursor.fetchall()
