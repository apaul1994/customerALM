from fastapi import APIRouter, HTTPException
from app.models.schemas import AnalyzeEntityRequest, AnalyzeEntityResponse, GetUrlContentRequest, GetUrlContentResponse, FetchArticleRequest, FetchArticleResponse
from app.services.customer_service import CustomerService
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
service = CustomerService()

@router.post("/analyze", response_model=AnalyzeEntityResponse)
async def analyze_entity(request: AnalyzeEntityRequest):
    """
    Endpoint to analyze an entity for matching score, criminal activity, and monetary fraud.
    Optionally fetches article content and date if URL is provided.

    Args:
        request: The request body containing entity details and optional URL.

    Returns:
        AnalyzeEntityResponse: The analysis result with optional content and date.
    """
    try:
        logger.info("Received analyze entity request")
        result = service.analyze_entity(request)
        logger.info("Analyze entity request processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing analyze entity request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.post("/geturlofcontent", response_model=GetUrlContentResponse)
async def get_url_content(request: GetUrlContentRequest):
    """
    Endpoint to fetch article content and date from a given URL.

    Args:
        request: The request body containing the URL.
    
    Returns:
        GetUrlContentResponse: The fetched article content and date.

    """
    try:
        logger.info("Received get URL content request")
        result = service.get_entity_articles(request.entity_name, request.country)
        logger.info("Get URL content request processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing get URL content request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/fetch-article", response_model=FetchArticleResponse)
async def fetch_article_endpoint(request: FetchArticleRequest):
    """
    Endpoint to fetch article content and date from a given URL.

    Args:
        request: The request body containing the URL.

    Returns:
        FetchArticleResponse: The fetched article content and date.
    """
    try:
        logger.info("Received fetch article request")
        content, date = service.fetch_article(request.url)
        logger.info("Fetch article request processed successfully")
        return FetchArticleResponse(content=content, date=date)
    except Exception as e:
        logger.error(f"Error processing fetch article request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")