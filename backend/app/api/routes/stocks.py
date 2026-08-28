from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class StockAnalysisPlaceholder(BaseModel):
    ticker: str
    status: str
    message: str
    supported_input: str


@router.get(
    "/{ticker}/analysis",
    response_model=StockAnalysisPlaceholder,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def get_stock_analysis(ticker: str) -> StockAnalysisPlaceholder:
    normalized_ticker = ticker.strip().upper()
    return StockAnalysisPlaceholder(
        ticker=normalized_ticker,
        status="not_implemented",
        message=(
            "Stock analysis is not implemented yet. The first version will only support "
            "US stock ticker input."
        ),
        supported_input="US stock ticker only",
    )

