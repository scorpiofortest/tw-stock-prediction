# Test Suite for Taiwan Stock Prediction & Paper Trading Backend

## Overview

This test suite provides comprehensive coverage for the backend system, following the test pyramid strategy:
- **65% Unit Tests** (~200 tests): Signal calculators, weighted scoring, portfolio logic
- **25% Integration Tests** (~60 tests): API endpoints, data pipeline, WebSocket, Groq AI
- **10% E2E Tests** (~20 tests): Complete user workflows with Playwright

**Target Coverage: ≥85% overall, ≥95% for P0 modules (signals, scoring, portfolio)**

## Directory Structure

```
tests/
├── unit/
│   ├── signals/              # 9 signal calculator tests
│   │   ├── test_outer_ratio.py
│   │   ├── test_bid_ask_pressure.py
│   │   ├── test_tick_direction.py
│   │   ├── test_intraday_position.py
│   │   ├── test_momentum.py
│   │   ├── test_rsi.py
│   │   ├── test_macd_osc.py
│   │   ├── test_kd_cross.py
│   │   └── test_trend_acceleration.py
│   ├── test_weighted_scoring.py   # Weighted scoring system tests
│   └── test_portfolio.py           # Paper trading portfolio tests
├── integration/
│   ├── test_data_pipeline.py      # Full data flow tests
│   ├── test_groq_integration.py   # AI service tests (mocked)
│   ├── test_verification_cycle.py # 62s verification tests
│   └── test_websocket.py          # WebSocket push tests
├── fixtures/
│   └── market_data/               # Test data scenarios
│       ├── bullish_scenario.json
│       ├── bearish_scenario.json
│       └── consolidation.json
├── conftest.py                    # Global fixtures
├── factories.py                   # Test data factories
└── README.md                      # This file
```

## Running Tests

### Install Test Dependencies

```bash
cd backend
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run all integration tests
pytest tests/integration/ -v

# Run all tests with coverage
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/signals/test_rsi.py -v

# Run tests matching pattern
pytest tests/ -k "test_buy" -v
```

### Run E2E Tests (Playwright)

```bash
# From project root
npx playwright test

# Run specific test file
npx playwright test tests/e2e/stock-analysis.spec.ts

# Run with UI mode
npx playwright test --ui

# Run with specific browser
npx playwright test --project=chromium
```

## Test Categories

### Unit Tests

#### Signal Calculator Tests
Each of the 9 signals has comprehensive tests covering:
- **Normal values**: Typical bullish, bearish, and neutral scenarios
- **Boundary values**: Extreme cases (0%, 100%, max, min)
- **Abnormal data**: None, negative values, zero division
- **Score range validation**: All scores must be -100 to +100

**Example**: `test_outer_ratio.py`
- Tests outer ratio from 0% to 100%
- Validates score mapping
- Handles edge cases like zero volume

#### Weighted Scoring Tests (`test_weighted_scoring.py`)
- Weights sum to 100%
- All signals have weights
- No negative weights
- Score always in -100 to +100
- Property-based testing (1000 random iterations)
- Partial signal handling (some None)
- High weight signal dominance

#### Portfolio Tests (`test_portfolio.py`)
**Buy Tests:**
- Normal buy, insufficient balance, exact balance
- Commission: max(floor(amount × 0.1425% × 0.6), 20)
- Zero/negative quantity handling

**Sell Tests:**
- Full/partial sell, exceed holdings, no position
- Tax: floor(amount × 0.3%) - sell only
- Realized PnL calculation

**PnL Tests:**
- Profit/loss with fees
- Unrealized PnL
- Total assets = cash + stock value
- Average cost after multiple buys

### Integration Tests

#### Data Pipeline (`test_data_pipeline.py`)
- Complete flow: raw data → signals → score → WebSocket push
- Partial data handling
- Data freshness validation
- Concurrent stock processing

#### Groq AI Integration (`test_groq_integration.py`)
- Request format validation
- Response parsing
- Timeout handling (10s)
- Rate limit retry (exponential backoff)
- Error handling and degradation
- AI toggle functionality
- Response caching (5 min TTL)

#### WebSocket (`test_websocket.py`)
- Connection management
- Stock subscription/unsubscription
- Broadcast to multiple clients
- Message format validation
- Heartbeat mechanism (30s ping, 90s timeout)

### E2E Tests (Playwright)

#### Stock Analysis Flow (`stock-analysis.spec.ts`)
- Search stock by code
- View 9 signals
- Verify weighted score
- AI analysis toggle
- Real-time WebSocket updates
- Invalid stock handling

#### Paper Trading Flow (`paper-trading.spec.ts`)
- Buy stock with balance check
- Sell stock with position check
- Commission & tax calculation
- Portfolio overview
- Transaction history
- Reset portfolio

## Test Fixtures

### Market Data Factories (`factories.py`)

```python
# Create bullish scenario
data = MarketDataFactory.create_bullish("2330")

# Create bearish scenario
data = MarketDataFactory.create_bearish("2317")

# Create custom scenario
data = MarketDataFactory.create(
    stock_id="2454",
    price=1056,
    prev_close=1055,
    outer_ratio=0.52
)
```

### JSON Fixtures

Located in `tests/fixtures/market_data/`:
- `bullish_scenario.json`: Strong buying pressure
- `bearish_scenario.json`: Strong selling pressure
- `consolidation.json`: Minimal movement

## Key Testing Constants

### Trading Costs
```python
FEE_RATE = 0.001425        # Commission rate: 0.1425%
FEE_DISCOUNT = 0.6         # 60% discount
MIN_FEE = 20.0             # Minimum fee: NT$20
TAX_RATE = 0.003           # Transaction tax: 0.3%
```

### Score Ranges
```python
SIGNAL_SCORE_MIN = -100
SIGNAL_SCORE_MAX = 100
CONFIDENCE_MIN = 10        # 10%
CONFIDENCE_MAX = 95        # 95%
```

### Verification Thresholds
```python
FLAT_THRESHOLD = 0.05      # ±0.05% for neutral predictions
```

## Coverage Reports

### Generate Coverage Report

```bash
# HTML report (interactive)
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=backend --cov-report=term-missing

# XML report (for CI)
pytest tests/ --cov=backend --cov-report=xml
```

### Coverage Targets

| Module | Line Coverage | Branch Coverage |
|--------|---------------|-----------------|
| Signal Calculators | ≥ 95% | ≥ 90% |
| Weighted Scoring | ≥ 95% | ≥ 90% |
| Portfolio Service | ≥ 90% | ≥ 85% |
| API Routes | ≥ 80% | ≥ 75% |
| **Overall Project** | **≥ 85%** | **≥ 80%** |

## CI/CD Integration

Tests run automatically on:
- Every push to main/develop
- Pull request creation
- Scheduled nightly builds

### GitHub Actions Workflow

```yaml
- name: Run Unit Tests
  run: pytest tests/unit/ -v --cov=backend --cov-report=xml

- name: Run Integration Tests
  run: pytest tests/integration/ -v

- name: Run E2E Tests
  run: npx playwright test

- name: Upload Coverage
  uses: codecov/codecov-action@v4
```

## Best Practices

### Writing Tests

1. **Use descriptive test names**: `test_buy_insufficient_balance_raises_error`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion per concept**: Focus on one behavior
4. **Use fixtures**: Avoid test data duplication
5. **Mock external dependencies**: Don't call real APIs
6. **Test edge cases**: Boundary values, None, negative, zero

### Example Test Structure

```python
def test_outer_ratio_all_outer_100_percent(self):
    """Outer ratio 100% (all outer volume)"""
    # Arrange
    outer = 1000
    inner = 0

    # Act
    ratio = calculate_outer_ratio(outer, inner)

    # Assert
    assert ratio == 1.0
    assert -100 <= score <= 100
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure backend is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Async Tests Not Running:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**E2E Tests Failing:**
```bash
# Install Playwright browsers
npx playwright install --with-deps
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Strategy Document](../docs/05-testing-strategy.md)

## Maintenance

- Update test data when signal formulas change
- Add tests for new features before implementation (TDD)
- Review and refactor tests during code reviews
- Monitor coverage trends in CI
- Update fixtures when market data structure changes

---

**Test Engineer Notes:**
- All tests use in-memory SQLite for speed
- WebSocket tests use mock connections
- Groq API is mocked to avoid costs and rate limits
- E2E tests run against local dev server
- Fixtures are designed to be realistic but deterministic
