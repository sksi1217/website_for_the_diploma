from dataclasses import dataclass
from typing import Optional


@dataclass
class Group:
    id: Optional[int]
    name: str
    course: int
    faculty: str


@dataclass
class Student:
    id: Optional[int]
    last_name: str
    first_name: str
    middle_name: str
    group_id: int
    student_id: str
    birth_date: str
    email: str
    phone: str
    status: str = 'Активный'

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


@dataclass
class Subject:
    id: Optional[int]
    name: str
    short_name: str
    teacher: str
    hours: int
    semester: int
    course: int
    subject_type: str


@dataclass
class Grade:
    id: Optional[int]
    student_id: int
    subject_id: int
    grade: int
    grade_type: str
    date: str
    semester: int
    teacher: str
    comment: str

    GRADE_TYPES = ['Четверть', 'Контрольная работа', 'Самостоятельная работа', 'Диктант', 'Проверочная работа']
    GRADE_LABELS = {5: 'Отлично', 4: 'Хорошо', 3: 'Удовлетворительно', 2: 'Неудовлетворительно'}
