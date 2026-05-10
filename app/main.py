from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ← добавить этот импорт

from app.api.auth.router import router as auth_router
from app.api.categories.router import router as categories_router
from app.api.skill_groups.router import router as skill_groups_router
from app.api.skills.router import router as skills_router
from app.api.skills_map.router import router as skills_map_router
from app.api.goals.router import router as goals_router
from app.api.github.router import router as github_router
from app.api.ai.ai_generator import router as ai_router
from app.api.admin.router import router as admin_router

# from app.api.ai.router import router as ai_router
from app.api.profile.router import router as profile_router
from app.api.dashboard.router import router as dashboard_router

app = FastAPI(
    title="SkillStack API",
    description="API for tracking and visualizing professional IT skills",
    version="0.1.0",
)

# ========== ДОБАВИТЬ CORS ЗДЕСЬ ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ========================================

# Подключаем все роутеры
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(skill_groups_router)
app.include_router(skills_router)
app.include_router(skills_map_router)
app.include_router(goals_router)
app.include_router(github_router)
app.include_router(profile_router)
app.include_router(dashboard_router)
app.include_router(ai_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "Welcome to SkillStack API", "docs": "/docs"}
