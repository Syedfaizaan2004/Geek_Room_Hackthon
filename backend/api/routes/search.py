import logging
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

from utils.company_lookup import search_company, get_suggestions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])

class SearchResponse(BaseModel):
    ticker: str
    company_name: str

class SuggestionResponse(BaseModel):
    suggestions: List[SearchResponse]

@router.get("/search-company", response_model=SearchResponse)
async def api_search_company(q: str = Query(..., min_length=1, description="Company name or partial name")):
    """
    Look up a company by name to find its ticker symbol.
    """
    result = search_company(q)
    if not result:
        raise HTTPException(status_code=404, detail=f"Company '{q}' not found.")
    return SearchResponse(**result)

@router.get("/suggest-company", response_model=SuggestionResponse)
async def api_suggest_company(q: str = Query(..., min_length=2, description="Prefix or substring to suggest from")):
    """
    Autocomplete endpoint returning multiple suggestions.
    """
    results = get_suggestions(q)
    # We always return an array, even if empty
    return SuggestionResponse(suggestions=[SearchResponse(**r) for r in results])
