from fastapi import APIRouter
from app.api.v1.endpoints.customer import router as customer_router

router = APIRouter()
router.include_router(customer_router, prefix="/customer", tags=["customer"])