from __future__ import annotations

from fastapi import FastAPI

from gex_app.web.routes import router

app = FastAPI(title="fq-gex", version="1.0.0")
app.include_router(router)
