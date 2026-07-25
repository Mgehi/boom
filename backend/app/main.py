import logging

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.db.base import engine
from app.routers import admin, auth, misc, pickups, shipments
from app.routers import settings as settings_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI()

# Signs the short-lived OAuth state/nonce cookie used during the Google login redirect round-trip.
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY, same_site="lax", https_only=True)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Delhivery Logistics Automation API", "status": "running"}


api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(shipments.router)
api_router.include_router(pickups.router)
api_router.include_router(settings_router.router)
api_router.include_router(misc.router)

app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    await engine.dispose()
