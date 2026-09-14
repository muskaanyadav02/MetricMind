"""Aggregates the version 1 routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import routes_chat, routes_health, routes_semantic, routes_validation

api_router = APIRouter()
api_router.include_router(routes_health.router)
api_router.include_router(routes_semantic.router)
api_router.include_router(routes_chat.router)
api_router.include_router(routes_validation.router)

__all__ = ["api_router"]
