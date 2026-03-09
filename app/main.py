from fastapi import FastAPI
from app.api.v1.router import router as v1_router
from app.core.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Customer Analyzer API",
    description="API for analyzing customer entities",
    version="1.0.0"
)

# Include routers
app.include_router(v1_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Customer Analyzer API")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Customer Analyzer API")

@app.get("/")
async def root():
    return {"message": "Welcome to Customer Analyzer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)