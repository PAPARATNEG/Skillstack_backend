# inspect_db.py (в корне проекта)
import sys
import os

# Добавляем путь к папке app, чтобы импорты работали
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine   # теперь database.py в папке app доступен
from sqlalchemy import inspect
from app.models.user import User
from app.models.category import Category
from app.models.skill_group import SkillGroup
from app.models.skill import Skill
from app.models.skill_node import SkillNode
from app.models.goal import Goal

def main():
    db = SessionLocal()
    try:
        # ... (весь ваш код main без изменений)
        users = db.query(User).all()
        print(f"\n=== Пользователи ({len(users)}) ===")
        for u in users:
            print(f"ID: {u.id}, username: {u.username}, email: {u.email}")

        cats = db.query(Category).all()
        print(f"\n=== Категории ({len(cats)}) ===")
        for c in cats:
            print(f"ID: {c.id}, name: {c.name}, is_system: {c.is_system}, user_id: {c.user_id}")

        groups = db.query(SkillGroup).all()
        print(f"\n=== Группы навыков ({len(groups)}) ===")
        for g in groups:
            print(f"ID: {g.id}, name: {g.name}, category_id: {g.category_id}, user_id: {g.user_id}")

        skills = db.query(Skill).limit(20).all()
        print(f"\n=== Навыки (первые {len(skills)}) ===")
        for s in skills:
            print(f"ID: {s.id}, name: {s.name}, level: {s.level}, group_id: {s.skill_group_id}, user_id: {s.user_id}")

        goals = db.query(Goal).limit(10).all()
        print(f"\n=== Цели (первые {len(goals)}) ===")
        for g in goals:
            print(f"ID: {g.id}, group_id: {g.skill_group_id}, target_level: {g.target_level}, deadline: {g.deadline}, completed: {g.is_completed}")

        nodes = db.query(SkillNode).limit(10).all()
        print(f"\n=== SkillNode (первые {len(nodes)}) ===")
        for n in nodes:
            print(f"skill_id: {n.skill_id}, x: {n.position_x}, y: {n.position_y}")
    finally:
        db.close()

if __name__ == "__main__":
    # Выводим структуру таблиц
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        print(f"\nТаблица: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"  {column['name']} : {column['type']}")
    # Выводим данные
    main()