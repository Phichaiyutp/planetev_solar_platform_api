from fastapi import FastAPI, APIRouter, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.routes import backend_api, tariff, report, fusionsolar ,auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await fusionsolar.scheduler_callback()
    await tariff.scheduler_callback()
    yield  

app = FastAPI(lifespan=lifespan)

""" origins = [
    "http://localhost",
    "http://localhost:3000",
] """

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

router.include_router(auth.router, prefix="/api/auth", tags=["auth"])
router.include_router(backend_api.router, prefix="/api/dashboard", tags=["backend_api"])
router.include_router(fusionsolar.router, prefix="/api/fusionsolar", tags=["fusionsolar"])
router.include_router(tariff.router, prefix="/api/tariff", tags=["tariff"])
router.include_router(report.router, prefix="/api/report", tags=["report"])

@router.get("/")
def read_data():
    try:
        payload = {"msg": "Hello"}
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

app.include_router(router)

