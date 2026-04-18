"""Custom exceptions for the application."""


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class InsufficientFunds(AppError):
    def __init__(self, message: str = "現金餘額不足"):
        super().__init__(message, code="INSUFFICIENT_FUNDS")


class InsufficientShares(AppError):
    def __init__(self, message: str = "持有股數不足"):
        super().__init__(message, code="INSUFFICIENT_SHARES")


class StockNotFound(AppError):
    def __init__(self, stock_id: str):
        super().__init__(f"找不到股票代碼: {stock_id}", code="STOCK_NOT_FOUND")


class QuoteUnavailable(AppError):
    def __init__(self, stock_id: str):
        super().__init__(f"無法取得報價: {stock_id}", code="QUOTE_UNAVAILABLE")


class AIServiceUnavailable(AppError):
    def __init__(self, message: str = "AI 分析服務暫時無法使用"):
        super().__init__(message, code="AI_UNAVAILABLE")
