import os
import csv
import io
import random
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request, Response

from database import Database
from demo_data import populate_school_demo
from utils import (
    validate_email, validate_phone, parse_date, format_date,
    format_csv_decimal, build_report_filename, csv_content_disposition,
)

app = Flask(__name__)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_performance.db")
db = Database(db_path)


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [row_to_dict(r) for r in rows]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())


@app.route("/api/meta")
def api_meta():
    """Группы, ученики и предметы для фильтров — один быстрый запрос."""
    return jsonify({
        "groups": rows_to_list(db.get_all_groups()),
        "students": rows_to_list(db.get_students_options()),
        "subjects": rows_to_list(db.get_all_subjects()),
        "stats": db.get_stats(),
    })


# ==================== GROUPS ====================

@app.route("/api/groups", methods=["GET"])
def api_groups_list():
    return jsonify(rows_to_list(db.get_all_groups()))


@app.route("/api/groups", methods=["POST"])
def api_groups_create():
    data = request.json
    try:
        gid = db.add_group(data["name"], int(data["course"]), data["faculty"])
        return jsonify({"id": gid, "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/groups/<int:gid>", methods=["PUT"])
def api_groups_update(gid):
    data = request.json
    try:
        db.update_group(gid, data["name"], int(data["course"]), data["faculty"])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/groups/<int:gid>", methods=["DELETE"])
def api_groups_delete(gid):
    try:
        db.delete_group(gid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ==================== STUDENTS ====================

@app.route("/api/students", methods=["GET"])
def api_students_list():
    search = request.args.get("search", "").strip()
    group_id = request.args.get("group_id", type=int)
    status = request.args.get("status")

    if search:
        students = db.search_students(search)
    else:
        students = db.get_all_students(group_id=group_id, status=status)

    averages = db.get_student_averages_map()
    result = []
    for s in students:
        d = row_to_dict(s)
        d["avg_grade"] = averages.get(s["id"], 0)
        d["birth_date_fmt"] = format_date(s["birth_date"]) if s["birth_date"] else ""
        result.append(d)
    return jsonify(result)


@app.route("/api/students/<int:sid>", methods=["GET"])
def api_students_get(sid):
    student = db.get_student_by_id(sid)
    if not student:
        return jsonify({"ok": False, "error": "Не найден"}), 404
    return jsonify(row_to_dict(student))


@app.route("/api/students", methods=["POST"])
def api_students_create():
    data = request.json
    err = _validate_student(data)
    if err:
        return jsonify({"ok": False, "error": err}), 400
    try:
        sid = db.add_student(
            data["last_name"], data["first_name"], data.get("middle_name", ""),
            data["group_id"], data["student_id"],
            data.get("birth_date"), data.get("email", ""), data.get("phone", ""),
            data.get("status", "Активный")
        )
        return jsonify({"id": sid, "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/students/<int:sid>", methods=["PUT"])
def api_students_update(sid):
    data = request.json
    err = _validate_student(data)
    if err:
        return jsonify({"ok": False, "error": err}), 400
    try:
        db.update_student(
            sid, data["last_name"], data["first_name"], data.get("middle_name", ""),
            data["group_id"], data["student_id"],
            data.get("birth_date"), data.get("email", ""), data.get("phone", ""),
            data.get("status", "Активный")
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/students/<int:sid>", methods=["DELETE"])
def api_students_delete(sid):
    db.delete_student(sid)
    return jsonify({"ok": True})


def _validate_student(data):
    if not all([data.get("last_name"), data.get("first_name"), data.get("student_id"), data.get("group_id")]):
        return "Заполните все обязательные поля!"
    if data.get("email") and not validate_email(data["email"]):
        return "Некорректный email! Пример: белова57@school15.edu.ru"
    if data.get("phone") and not validate_phone(data["phone"]):
        return "Некорректный телефон! Только цифры, 10–15 знаков (например: +79001234567)"
    if data.get("birth_date"):
        parsed = parse_date(data["birth_date"]) if "-" not in data["birth_date"][:4] else data["birth_date"]
        if not parsed:
            return "Формат даты: ДД.ММ.ГГГГ"
        data["birth_date"] = parsed
    else:
        data["birth_date"] = None
    return None


# ==================== SUBJECTS ====================

@app.route("/api/subjects", methods=["GET"])
def api_subjects_list():
    return jsonify(rows_to_list(db.get_all_subjects()))


@app.route("/api/subjects", methods=["POST"])
def api_subjects_create():
    data = request.json
    if not data.get("name"):
        return jsonify({"ok": False, "error": "Введите название!"}), 400
    try:
        sid = db.add_subject(
            data["name"], data.get("short_name", ""), data.get("teacher", ""),
            int(data.get("hours", 0)), int(data["semester"]), int(data["course"]),
            data.get("subject_type", "Лекция")
        )
        return jsonify({"id": sid, "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/subjects/<int:sid>", methods=["PUT"])
def api_subjects_update(sid):
    data = request.json
    if not data.get("name"):
        return jsonify({"ok": False, "error": "Введите название!"}), 400
    try:
        db.update_subject(
            sid, data["name"], data.get("short_name", ""), data.get("teacher", ""),
            int(data.get("hours", 0)), int(data["semester"]), int(data["course"]),
            data.get("subject_type", "Лекция")
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/subjects/<int:sid>", methods=["DELETE"])
def api_subjects_delete(sid):
    db.delete_subject(sid)
    return jsonify({"ok": True})


# ==================== GRADES ====================

@app.route("/api/grades", methods=["GET"])
def api_grades_list():
    student_id = request.args.get("student_id", type=int)
    subject_id = request.args.get("subject_id", type=int)
    semester = request.args.get("semester", type=int)
    limit = request.args.get("limit", 300, type=int)
    total = db.count_grades(student_id=student_id, subject_id=subject_id, semester=semester)
    grades = db.get_grades(
        student_id=student_id, subject_id=subject_id, semester=semester, limit=limit
    )
    result = []
    for g in grades:
        d = row_to_dict(g)
        d["date_fmt"] = format_date(g["date"])
        result.append(d)
    return jsonify({"rows": result, "total": total, "shown": len(result)})


@app.route("/api/grades/<int:gid>", methods=["GET"])
def api_grades_get(gid):
    grade = db.get_grade_by_id(gid)
    if not grade:
        return jsonify({"ok": False, "error": "Не найдено"}), 404
    d = row_to_dict(grade)
    d["date_fmt"] = format_date(grade["date"])
    return jsonify(d)


@app.route("/api/grades", methods=["POST"])
def api_grades_create():
    data = request.json
    err = _validate_grade(data)
    if err:
        return jsonify({"ok": False, "error": err}), 400
    try:
        gid = db.add_grade(
            data["student_id"], data["subject_id"], int(data["grade"]),
            data["grade_type"], data["date"], int(data["semester"]),
            data.get("teacher", ""), data.get("comment", "")
        )
        return jsonify({"id": gid, "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/grades/<int:gid>", methods=["PUT"])
def api_grades_update(gid):
    data = request.json
    err = _validate_grade(data)
    if err:
        return jsonify({"ok": False, "error": err}), 400
    try:
        db.update_grade(
            gid, data["student_id"], data["subject_id"], int(data["grade"]),
            data["grade_type"], data["date"], int(data["semester"]),
            data.get("teacher", ""), data.get("comment", "")
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/grades/<int:gid>", methods=["DELETE"])
def api_grades_delete(gid):
    db.delete_grade(gid)
    return jsonify({"ok": True})


def _validate_grade(data):
    if not all([data.get("student_id"), data.get("subject_id"), data.get("grade"), data.get("date")]):
        return "Заполните обязательные поля!"
    parsed = parse_date(data["date"]) if "." in str(data["date"]) else data["date"]
    if not parsed:
        return "Формат даты: ДД.ММ.ГГГГ"
    data["date"] = parsed
    return None


# ==================== REPORTS ====================

@app.route("/api/reports/group_stat")
def api_report_group_stat():
    group_id = request.args.get("group_id", type=int)
    semester = request.args.get("semester", type=int)

    if not group_id:
        groups = db.get_all_groups()
        if not groups:
            return jsonify({"rows": [], "info": "Нет групп"})
        group_id = groups[0]["id"]

    data = db.get_group_statistics(group_id, semester)
    rows = []
    total_avg = 0
    count = 0
    for row in data:
        name = f"{row['last_name']} {row['first_name']} {row['middle_name'] or ''}".strip()
        avg = round(row["avg_grade"], 2) if row["avg_grade"] else 0
        total_avg += avg
        count += 1
        tag = "excellent" if avg >= 4.5 else ("failing" if (row["twos"] or 0) > 0 else "")
        rows.append({
            "name": name, "student_number": row["student_number"],
            "grades_count": row["grades_count"] or 0,
            "avg": f"{avg:.2f}" if avg else "—",
            "fives": row["fives"] or 0, "fours": row["fours"] or 0,
            "threes": row["threes"] or 0, "twos": row["twos"] or 0,
            "tag": tag
        })
    avg_total = total_avg / count if count else 0
    return jsonify({
        "rows": rows,
        "info": f"Студентов: {count} | Средний балл группы: {avg_total:.2f}"
    })


@app.route("/api/reports/subject_stat")
def api_report_subject_stat():
    data = db.get_subject_statistics()
    rows = []
    for row in data:
        avg = round(row["avg_grade"], 2) if row["avg_grade"] else 0
        rows.append({
            "subject_name": row["subject_name"], "total_grades": row["total_grades"] or 0,
            "avg": f"{avg:.2f}" if avg else "—",
            "fives": row["fives"] or 0, "fours": row["fours"] or 0,
            "threes": row["threes"] or 0, "twos": row["twos"] or 0
        })
    return jsonify({"rows": rows, "info": f"Предметов: {len(data)}"})


@app.route("/api/reports/excellent")
def api_report_excellent():
    group_id = request.args.get("group_id", type=int)
    data = db.get_excellent_students(group_id)
    rows = []
    for row in data:
        name = f"{row['last_name']} {row['first_name']} {row['middle_name'] or ''}".strip()
        rows.append({
            "name": name, "student_number": row["student_number"],
            "group_name": row["group_name"],
            "avg": f"{row['avg_grade']:.2f}", "grades_count": row["grades_count"],
            "tag": "excellent"
        })
    return jsonify({"rows": rows, "info": f"Отличников: {len(data)}"})


@app.route("/api/reports/failing")
def api_report_failing():
    group_id = request.args.get("group_id", type=int)
    data = db.get_failing_students(group_id)
    rows = []
    for row in data:
        name = f"{row['last_name']} {row['first_name']} {row['middle_name'] or ''}".strip()
        rows.append({
            "name": name, "student_number": row["student_number"],
            "group_name": row["group_name"], "debt_count": row["debt_count"],
            "tag": "failing"
        })
    return jsonify({"rows": rows, "info": f"Студентов с долгами: {len(data)}"})


@app.route("/api/reports/distribution")
def api_report_distribution():
    data = db.get_grade_distribution()
    labels = {5: "Отлично", 4: "Хорошо", 3: "Удовл.", 2: "Неудовл."}
    colors = {5: "#27ae60", 4: "#2980b9", 3: "#e67e22", 2: "#e74c3c"}
    total = sum(r["count"] for r in data)
    rows = []
    for row in data:
        pct = round(row["count"] / total * 100, 1) if total else 0
        grade = row["grade"]
        rows.append({
            "grade": grade, "label": labels.get(grade, ""),
            "count": row["count"], "percent": f"{pct}%",
            "color": colors.get(grade, "black")
        })
    return jsonify({"rows": rows, "info": f"Всего оценок: {total}"})


@app.route("/api/reports/student_card")
def api_report_student_card():
    student_id = request.args.get("student_id", type=int)
    if not student_id:
        return jsonify({"rows": [], "info": ""})
    grades = db.get_grades(student_id=student_id)
    grade_labels = {5: "5 — Отлично", 4: "4 — Хорошо", 3: "3 — Удовл.", 2: "2 — Неудовл."}
    grade_colors = {5: "#27ae60", 4: "#2980b9", 3: "#e67e22", 2: "#e74c3c"}
    rows = []
    for g in grades:
        gv = g["grade"]
        rows.append({
            "subject_name": g["subject_name"],
            "grade": grade_labels.get(gv, str(gv)),
            "grade_type": g["grade_type"], "date": g["date"],
            "semester": g["semester"], "teacher": g["teacher"] or "",
            "color": grade_colors.get(gv, "black")
        })
    avg = db.get_student_average(student_id)
    return jsonify({
        "rows": rows,
        "info": f"Оценок: {len(grades)} | Средний балл: {avg:.2f}"
    })


@app.route("/api/reports/export")
def api_report_export():
    try:
        report = request.args.get("report", "group_stat")
        handlers = {
            "group_stat": api_report_group_stat,
            "subject_stat": api_report_subject_stat,
            "excellent": api_report_excellent,
            "failing": api_report_failing,
            "distribution": api_report_distribution,
            "student_card": api_report_student_card,
        }
        data = handlers.get(report, api_report_group_stat)().get_json()

        if not data.get("rows"):
            return jsonify({"ok": False, "error": "Нет данных для экспорта"}), 400

        headers_map = {
            "group_stat": ["ФИО", "№ Зачётки", "Оценок", "Ср. балл", "5", "4", "3", "2"],
            "subject_stat": ["Предмет", "Оценок", "Ср. балл", "5", "4", "3", "2"],
            "excellent": ["ФИО", "№ Зачётки", "Группа", "Ср. балл", "Оценок"],
            "failing": ["ФИО", "№ Зачётки", "Группа", "Долгов"],
            "distribution": ["Оценка", "Словесно", "Количество", "Процент"],
            "student_card": ["Предмет", "Оценка", "Тип", "Дата", "Семестр", "Преподаватель"],
        }
        keys_map = {
            "group_stat": ["name", "student_number", "grades_count", "avg", "fives", "fours", "threes", "twos"],
            "subject_stat": ["subject_name", "total_grades", "avg", "fives", "fours", "threes", "twos"],
            "excellent": ["name", "student_number", "group_name", "avg", "grades_count"],
            "failing": ["name", "student_number", "group_name", "debt_count"],
            "distribution": ["grade", "label", "count", "percent"],
            "student_card": ["subject_name", "grade", "grade_type", "date", "semester", "teacher"],
        }
        decimal_keys = {"avg", "percent"}

        output = io.StringIO()
        output.write("sep=;\r\n")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(headers_map.get(report, []))
        for row in data["rows"]:
            cells = []
            for k in keys_map.get(report, []):
                val = row.get(k, "")
                if k in decimal_keys:
                    val = format_csv_decimal(val, decimals=1 if k == "percent" else 2)
                    if k == "percent" and val:
                        val = f"{val}%"
                cells.append(val)
            writer.writerow(cells)

        filename = build_report_filename(
            report,
            db,
            group_id=request.args.get("group_id", type=int),
            student_id=request.args.get("student_id", type=int),
            semester=request.args.get("semester", type=int),
        )
        return Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": csv_content_disposition(filename)},
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Ошибка экспорта: {e}"}), 500


# ==================== DATA MANAGEMENT ====================

@app.route("/api/demo", methods=["POST"])
def api_load_demo():
    try:
        stats = populate_school_demo(
            db, students_per_class=(6, 10), grades_range=(4, 7), clear_first=True
        )
        return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/demo/seed-if-empty", methods=["POST"])
def api_seed_if_empty():
    """Заполняет БД демо-данными, если она пустая."""
    stats = db.get_stats()
    if stats["students"] > 0:
        return jsonify({"ok": True, "seeded": False, "stats": stats})
    stats = populate_school_demo(
        db, students_per_class=(6, 10), grades_range=(4, 7), clear_first=False
    )
    return jsonify({"ok": True, "seeded": True, "stats": stats})


@app.route("/api/clear", methods=["POST"])
def api_clear_data():
    db.clear_all_data()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
