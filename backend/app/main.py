from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    b2b,
    catalog,
    customers,
    health,
    offers,
    ops,
    party_prices,
    platform,
    public,
    purchase_orders,
    sales_orders,
    stock_ops,
    store,
    suppliers,
    uploads,
    users_api,
)
from app.config import get_settings
from app.core.responses import error


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exc_handler(_: Request, exc: HTTPException):
        msg = exc.detail if isinstance(exc.detail, str) else "Error"
        return error(msg, status_code=exc.status_code, err=msg)

    prefix = "/api"
    app.include_router(health.router, prefix=prefix)
    app.include_router(public.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(platform.router, prefix=prefix)
    app.include_router(customers.router, prefix=prefix)
    app.include_router(catalog.router, prefix=prefix)
    app.include_router(suppliers.router, prefix=prefix)
    app.include_router(offers.router, prefix=prefix)
    app.include_router(users_api.router, prefix=prefix)
    app.include_router(ops.router, prefix=prefix)
    app.include_router(purchase_orders.router, prefix=prefix)
    app.include_router(sales_orders.router, prefix=prefix)
    app.include_router(stock_ops.router, prefix=prefix)
    app.include_router(store.router, prefix=prefix)
    app.include_router(b2b.router, prefix=prefix)
    app.include_router(party_prices.router, prefix=prefix)
    app.include_router(uploads.router, prefix=prefix)

    return app


app = create_app()
