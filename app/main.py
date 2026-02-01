from fastapi import FastAPI
from app.api.auth.router import router as auth_router

app = FastAPI(title="SkillStack API")

app.include_router(auth_router)