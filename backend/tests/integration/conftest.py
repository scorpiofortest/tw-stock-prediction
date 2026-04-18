"""
Integration test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async integration tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_server():
    """
    Start test server for integration tests
    This will be implemented when FastAPI app is ready
    """
    # TODO: Start test server
    # server = TestServer(app)
    # await server.start()
    # yield server
    # await server.stop()
    pass


@pytest.fixture
def mock_groq_api(mocker):
    """
    Mock Groq API responses for integration tests
    Avoids actual API calls during testing
    """
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"summary":"短線偏多","outlook":"short_term_bullish","key_factors":["均線多頭排列","成交量放大","法人買超"],"risk_level":"medium","suggestion":"可考慮布局"}'
            }
        }],
        "usage": {"total_tokens": 450}
    }

    # Mock the Groq API call
    # mocker.patch('backend.services.ai_analysis.groq_client.chat.completions.create', return_value=mock_response)

    return mock_response


@pytest.fixture
def sample_market_data_full():
    """Complete market data for integration testing"""
    return {
        "stock_id": "2330",
        "stock_name": "台積電",
        "price": {
            "open": 891.0,
            "high": 910.0,
            "low": 888.0,
            "close": 905.0,
            "prev_close": 880.0,
        },
        "volume": {
            "total": 50000,
            "outer": 36000,
            "inner": 14000,
        },
        "order_book": {
            "bid": [
                {"price": 904, "qty": 500},
                {"price": 903, "qty": 450},
                {"price": 902, "qty": 400},
                {"price": 901, "qty": 350},
                {"price": 900, "qty": 300},
            ],
            "ask": [
                {"price": 905, "qty": 50},
                {"price": 906, "qty": 45},
                {"price": 907, "qty": 40},
                {"price": 908, "qty": 35},
                {"price": 909, "qty": 30},
            ],
        },
        "technical": {
            "rsi_14": 68.5,
            "macd": {"dif": 3.2, "macd": 2.1, "osc": 1.1},
            "kd": {"k": 75.2, "d": 68.3},
        },
    }
