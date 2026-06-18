"""
Скрипт для заполнения базы данных тестовыми данными.
Запуск: python fill_database.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from demo_data import populate_school_demo


def fill_database():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "student_performance.db")
    db = Database(db_path)

    print("=" * 60)
    print("  Заполнение базы данных тестовыми данными (школа)")
    print("=" * 60)

    stats = populate_school_demo(
        db, students_per_class=(6, 10), grades_range=(4, 7), clear_first=True
    )

    print("\n" + "=" * 60)
    print("  ИТОГ:")
    print(f"  • Классов:   {stats['groups']}")
    print(f"  • Предметов: {stats['subjects']}")
    print(f"  • Учеников:  {stats['students']}")
    print(f"  • Оценок:    {stats['grades']}")
    print("=" * 60)
    print("\n  ✅ База данных успешно заполнена!")
    print("  Теперь запустите main.py\n")

    db.close()


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "student_performance.db")

    if os.path.exists(db_path):
        db_check = Database(db_path)
        students_count = len(db_check.get_all_students())
        db_check.close()

        if students_count > 0:
            print(f"⚠️  В базе уже есть {students_count} учеников.")
            answer = input("Добавить ещё тестовые данные? (да/нет): ").strip().lower()
            if answer not in ("да", "д", "yes", "y"):
                print("Отменено.")
                sys.exit(0)

    fill_database()
