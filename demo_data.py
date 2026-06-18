"""Генерация демо-данных для школьной АИС."""

import random
from datetime import datetime, timedelta


GROUPS_DATA = [
    ("5А", 5, "Начальная школа"),
    ("5Б", 5, "Начальная школа"),
    ("6А", 6, "Начальная школа"),
    ("7А", 7, "Среднее звено"),
    ("7Б", 7, "Среднее звено"),
    ("8В", 8, "Среднее звено"),
    ("9А", 9, "Среднее звено"),
    ("9В", 9, "Среднее звено"),
    ("10А", 10, "Старшие классы"),
    ("11А", 11, "Старшие классы"),
    ("11Б", 11, "Старшие классы"),
]

SUBJECTS_DATA = [
    ("Математика", "Мат.", "Иванова Светлана Петровна", 136, 1, 5, "Урок"),
    ("Русский язык", "Рус.", "Петрова Ольга Ивановна", 170, 1, 5, "Урок"),
    ("Литература", "Лит.", "Петрова Ольга Ивановна", 68, 2, 5, "Урок"),
    ("Окружающий мир", "ОкрМир", "Сидорова Анна Сергеевна", 68, 1, 4, "Урок"),
    ("История", "Ист.", "Морозов Виктор Алексеевич", 68, 2, 7, "Урок"),
    ("Физика", "Физ.", "Козлов Андрей Борисович", 68, 2, 7, "Урок"),
    ("Биология", "Био.", "Новикова Елена Павловна", 51, 2, 7, "Урок"),
    ("Английский язык", "Англ.", "Белова Наталья Владимировна", 102, 1, 7, "Урок"),
    ("Информатика", "Инф.", "Волков Денис Сергеевич", 34, 3, 7, "Практика"),
    ("География", "Геогр.", "Орлова Дарья Михайловна", 51, 3, 8, "Урок"),
    ("Обществознание", "Общ.", "Соколов Геннадий Борисович", 51, 2, 9, "Урок"),
    ("Алгебра", "Алг.", "Иванова Светлана Петровна", 102, 1, 9, "Урок"),
    ("Геометрия", "Геом.", "Иванова Светлана Петровна", 85, 2, 9, "Урок"),
    ("Химия", "Хим.", "Зайцева Ирина Олеговна", 51, 3, 9, "Лабораторная"),
    ("Физика (ст.)", "Физ11", "Козлов Андрей Борисович", 102, 1, 11, "Урок"),
    ("Русский (ст.)", "Рус11", "Петрова Ольга Ивановна", 102, 1, 11, "Урок"),
    ("Подготовка к ЕГЭ", "ЕГЭ", "Иванова Светлана Петровна", 68, 4, 11, "Урок"),
    ("Физическая культура", "Физ-ра", "Лебедев Станислав Юрьевич", 68, 1, 8, "Урок"),
    ("Музыка", "Муз.", "Щербакова Ирина Геннадьевна", 34, 2, 5, "Урок"),
    ("Технология", "Техн.", "Попова Анна Дмитриевна", 34, 3, 5, "Практика"),
]

LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Козлов", "Новиков", "Морозов", "Волков",
    "Зайцев", "Попов", "Соколов", "Лебедев", "Козлова", "Новикова", "Морозова",
    "Волкова", "Орлов", "Федоров", "Михайлов", "Беляев", "Тарасов", "Белова",
    "Комаров", "Орлова", "Киселёв", "Макаров", "Андреев", "Алексеев", "Степанов",
    "Яковлев", "Борисов", "Кузнецов", "Смирнов", "Попова", "Соколова", "Лебедева",
    "Захаров", "Семёнов", "Голубев", "Виноградов", "Богданов",
]

MALE_NAMES = [
    "Александр", "Дмитрий", "Сергей", "Андрей", "Алексей", "Максим", "Артём",
    "Роман", "Илья", "Павел", "Кирилл", "Денис", "Антон", "Владимир", "Николай",
]

FEMALE_NAMES = [
    "Мария", "Анна", "Елена", "Ольга", "Наталья", "Светлана", "Ирина", "Юлия",
    "Екатерина", "Дарья", "Татьяна", "Алина", "Виктория", "Ксения", "Валерия",
]

MALE_PATRONYMICS = [
    "Иванович", "Петрович", "Сергеевич", "Андреевич", "Алексеевич",
    "Дмитриевич", "Николаевич", "Владимирович", "Олегович",
]

FEMALE_PATRONYMICS = [
    "Ивановна", "Петровна", "Сергеевна", "Андреевна", "Алексеевна",
    "Дмитриевна", "Николаевна", "Владимировна", "Олеговна",
]

GRADE_TYPES = [
    "Четверть", "Контрольная работа", "Самостоятельная работа",
    "Диктант", "Проверочная работа",
]

TEACHERS = [
    "Иванова С.П.", "Петрова О.И.", "Козлов А.Б.", "Сидорова А.С.",
    "Волков Д.С.", "Зайцева И.О.", "Морозов В.А.", "Орлова Д.М.",
    "Лебедев С.Ю.", "Белова Н.В.", "Щербакова И.Г.",
]

GRADE_PROFILES = {
    "отличник": [5, 5, 5, 5, 4],
    "хорошист": [5, 4, 4, 4, 3],
    "средний": [4, 3, 3, 3, 2],
    "троечник": [3, 3, 3, 2, 2],
    "должник": [3, 2, 2, 2, 2],
}

GRADE_COMMENTS = {
    5: "Отличная работа",
    4: "Хороший результат",
    3: "Удовлетворительно",
    2: "Требуется доработка",
}


def populate_school_demo(db, students_per_class=(6, 10), grades_range=(4, 7), clear_first=False):
    """Заполняет БД школьными демо-данными. Возвращает статистику."""
    if clear_first:
        db.clear_all_data()

    group_ids = {}
    for name, course, faculty in GROUPS_DATA:
        group_ids[name] = db.add_group(name, course, faculty)

    subject_ids = [db.add_subject(*data) for data in SUBJECTS_DATA]

    student_ids = []
    counter = 1
    grade_rows = []

    for group_name, group_id in group_ids.items():
        class_grade = int("".join(c for c in group_name if c.isdigit()) or 5)
        num_students = random.randint(*students_per_class)

        for i in range(num_students):
            is_male = random.choice([True, False])
            if is_male:
                first_name = random.choice(MALE_NAMES)
                patronymic = random.choice(MALE_PATRONYMICS)
                last_name = random.choice([
                    l for l in LAST_NAMES if not l.endswith("а") and not l.endswith("ва")
                ])
            else:
                first_name = random.choice(FEMALE_NAMES)
                patronymic = random.choice(FEMALE_PATRONYMICS)
                last_name = random.choice([
                    l for l in LAST_NAMES if l.endswith("а") or l.endswith("ва")
                ])

            student_number = f"{group_name}-{str(i + 1).zfill(3)}"
            counter += 1
            age = class_grade + 6 + random.randint(0, 1)
            birth_date = (datetime.now() - timedelta(days=age * 365 + random.randint(0, 300))).strftime("%Y-%m-%d")
            email = f"{last_name.lower()}{counter}@school15.edu.ru"
            phone = f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}"
            statuses = ["Активный"] * 9 + ["Академический отпуск", "Отчислен"]
            status = random.choice(statuses)

            sid = db.add_student(
                last_name, first_name, patronymic, group_id,
                student_number, birth_date, email, phone, status
            )
            student_ids.append(sid)

            profile = GRADE_PROFILES[random.choices(
                list(GRADE_PROFILES.keys()),
                weights=[10, 30, 30, 20, 10]
            )[0]]
            num_grades = random.randint(*grades_range)
            for subj_id in random.sample(subject_ids, min(num_grades, len(subject_ids))):
                grade = random.choice(profile)
                grade_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
                grade_rows.append((
                    sid, subj_id, grade,
                    random.choice(GRADE_TYPES), grade_date,
                    random.randint(1, 4), random.choice(TEACHERS),
                    GRADE_COMMENTS.get(grade, "")
                ))

    db.add_grades_bulk(grade_rows)

    return {
        "groups": len(db.get_all_groups()),
        "subjects": len(db.get_all_subjects()),
        "students": len(db.get_all_students()),
        "grades": len(db.get_grades()),
        "added_grades": len(grade_rows),
    }
