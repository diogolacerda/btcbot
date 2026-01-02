from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health

app = FastAPI(title="BTC Grid Bot API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar depois
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
