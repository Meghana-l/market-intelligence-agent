from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, query, stocks
from app.core.config import settings
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/api")
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ARIA backend is running"}
