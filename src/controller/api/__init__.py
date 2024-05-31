"""API Router."""

from fastapi import APIRouter

from src.controller.api.endpoints import transactions

router = APIRouter()
router.include_router(transactions.router)
