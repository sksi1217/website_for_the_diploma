import re
import re
from datetime import datetime


def validate_email(email):
    if not email:
        return True
    email = email.strip()
    if len(email) > 254:
        return False
    # Локальная часть: кириллица и латиница; домен: только ASCII (без букв после .ru и т.п.)
    pattern = (
        r'^[a-zA-Z0-9._%+\u0400-\u04FF-]+'
        r'@'
        r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
    )
    return bool(re.fullmatch(pattern, email))


def validate_phone(phone):
    if not phone:
        return True
    cleaned = re.sub(r'[\s\-().]', '', phone.strip())
    return bool(re.fullmatch(r'\+?\d{10,15}', cleaned))


def format_date(date_str):
    if not date_str:
        return ''
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d.%m.%Y')
    except:
        return date_str


def parse_date(date_str):
    for fmt in ['%d.%m.%Y', '%Y-%m-%d']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except:
            continue
    return None


def grade_to_text(grade):
    labels = {5: 'Отлично', 4: 'Хорошо', 3: 'Удовлетворительно', 2: 'Неудовлетворительно'}
    return labels.get(grade, str(grade))


def grade_color(grade):
    colors = {5: '#27ae60', 4: '#2980b9', 3: '#f39c12', 2: '#e74c3c'}
    return colors.get(grade, '#2c3e50')


def generate_student_id(last_name, year=None):
    if year is None:
        year = datetime.now().year % 100
    prefix = last_name[:2].upper() if last_name else 'ST'
    import random
    return f"{prefix}{year}{random.randint(1000, 9999)}"


def format_csv_decimal(value, decimals=2):
    """Формат дробного числа для CSV в русской локали Excel (запятая вместо точки)."""
    if value is None or value == "" or value == "—":
        return ""
    if isinstance(value, str):
        value = value.replace("%", "").strip().replace(",", ".")
        if not value:
            return ""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{num:.{decimals}f}".replace(".", ",")


def encode_csv_for_excel(csv_text):
    """Windows-1251: стандартная кодировка CSV для русского Excel."""
    csv_text = csv_text.replace("—", "-").replace("–", "-")
    return csv_text.encode("cp1251", errors="replace")


def sanitize_filename_part(text, max_len=50):
    text = re.sub(r'[\\/:*?"<>|]+', "", str(text or "").strip())
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_len]


def build_report_filename(report, db, group_id=None, student_id=None, semester=None):
    """Понятное имя CSV-файла по типу отчёта и параметрам."""
    group_name = ""
    if group_id:
        for g in db.get_all_groups():
            if g["id"] == group_id:
                group_name = g["name"]
                break

    student_part = ""
    if student_id:
        st = db.get_student_by_id(student_id)
        if st:
            student_part = sanitize_filename_part(f"{st['last_name']}_{st['first_name']}")

    if report == "group_stat":
        if group_id:
            parts = ["Успеваемость_группы", sanitize_filename_part(group_name)]
        else:
            parts = ["Успеваемость_всех_групп"]
        if semester:
            parts.append(f"семестр_{semester}")
    elif report == "subject_stat":
        parts = ["Успеваемость_по_предметам"]
    elif report == "excellent":
        parts = ["Отличники", sanitize_filename_part(group_name)] if group_name else ["Отличники"]
    elif report == "failing":
        parts = ["Должники", sanitize_filename_part(group_name)] if group_name else ["Должники"]
    elif report == "distribution":
        parts = ["Распределение_оценок"]
    elif report == "student_card":
        parts = ["Карточка_студента", student_part] if student_part else ["Карточка_студента"]
    else:
        parts = ["Отчет"]

    parts = [p for p in parts if p]
    date = datetime.now().strftime("%Y-%m-%d")
    return f"{'_'.join(parts)}_{date}.csv"


def csv_content_disposition(filename):
    """Заголовок Content-Disposition с поддержкой кириллицы в имени файла."""
    from urllib.parse import quote

    # filename= должен быть только ASCII (требование HTTP), иначе сервер падает
    ascii_fallback = re.sub(r"[^A-Za-z0-9._\-]", "_", filename) or "report.csv"
    encoded = quote(filename, safe="")
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded}'
