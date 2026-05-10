import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"User: {u.username}, email: {u.email}")
    print(f"  password_hash: {u.password_hash[:50]}..." if u.password_hash else "  password_hash: None")
    print(f"  length: {len(u.password_hash) if u.password_hash else 0}")
    print()
db.close()