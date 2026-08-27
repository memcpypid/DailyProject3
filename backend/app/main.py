import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.infrastructure.db import Base, engine
from app.infrastructure import models  # noqa: F401  (register models on Base.metadata)

logger = logging.getLogger(__name__)
settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# Struktur error API disamakan di seluruh endpoint: body JSON selalu punya
# `detail` berupa STRING (bukan array/objek FastAPI bawaan untuk error 422,
# dan bukan teks polos seperti "Internal Server Error" untuk error tak terduga)
# supaya frontend bisa selalu menampilkan pesan errornya lewat
# `err.response?.data?.detail` tanpa perlu menebak bentuk datanya.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    detail = "; ".join(f"{e['field']}: {e['message']}" for e in errors) or "Data yang dikirim tidak valid"
    return JSONResponse(status_code=422, content={"detail": detail, "errors": errors})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error saat memproses %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Terjadi kesalahan pada server. Silakan coba lagi."})
