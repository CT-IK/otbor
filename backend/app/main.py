from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.schedule import router as schedule_router


app = FastAPI(title="Zapis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"]) 
app.include_router(auth_router, prefix="/api", tags=["auth"]) 
app.include_router(profile_router, prefix="/api", tags=["profile"]) 
app.include_router(schedule_router, prefix="/api", tags=["schedule"]) 

