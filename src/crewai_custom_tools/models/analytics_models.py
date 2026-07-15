"""Pydantic models for the analytics tools (valuation, ETF metrics)."""

from pydantic import BaseModel, Field


class ValuationInput(BaseModel):
    """Input schema for valuation calculations."""

    ticker: str = Field(..., description="Stock ticker symbol")
    current_price: float = Field(..., description="Current market price")

    # DCF inputs (optional)
    cash_flows: list[float] | None = Field(None, description="Projected annual free cash flows")
    discount_rate: float | None = Field(None, description="Discount rate (WACC) as decimal")
    terminal_growth: float | None = Field(None, description="Terminal growth rate as decimal")
    shares_outstanding: float | None = Field(None, description="Number of shares outstanding")

    # P/E inputs (optional)
    earnings_per_share: float | None = Field(None, description="Earnings per share")
    target_pe_ratio: float | None = Field(None, description="Target P/E multiple")
    sector_avg_pe: float | None = Field(None, description="Sector average P/E")

    # Technical inputs (optional)
    price_history: list[float] | None = Field(None, description="Historical prices for technical analysis")


class ETFAnalysisInput(BaseModel):
    """Input schema for ETF analysis."""

    ticker: str = Field(..., description="ETF ticker symbol")

    # Returns data (optional)
    etf_returns: list[float] | None = Field(None, description="ETF return series")
    benchmark_returns: list[float] | None = Field(None, description="Benchmark return series")

    # ETF characteristics (optional)
    expense_ratio: float | None = Field(None, description="Annual expense ratio as decimal")
    avg_daily_volume: float | None = Field(None, description="Average daily trading volume")
    bid_ask_spread_pct: float | None = Field(None, description="Bid-ask spread as percentage")
    market_cap: float | None = Field(None, description="Market capitalization")

    # Holdings data (optional)
    holdings: list[dict[str, float]] | None = Field(None, description="List of holdings with 'weight' key (as decimal)")
