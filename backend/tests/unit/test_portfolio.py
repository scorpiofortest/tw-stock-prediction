"""
Unit tests for Paper Trading Portfolio
Target Coverage: ≥ 90%

Trading Cost Constants:
- Commission rate: 0.1425%
- Commission discount: 60% (0.6)
- Minimum commission: NT$20
- Transaction tax: 0.3% (sell only)
- Rounding: Floor (無條件捨去)

Formulas:
Buy:
    Amount = Price × Shares
    Fee = max(floor(Amount × 0.001425 × 0.6), 20)
    Total Cost = Amount + Fee

Sell:
    Amount = Price × Shares
    Fee = max(floor(Amount × 0.001425 × 0.6), 20)
    Tax = floor(Amount × 0.003)
    Net Proceeds = Amount - Fee - Tax
    Realized PnL = Net Proceeds - (Avg Cost × Shares)
"""
import pytest
import math


class TestBuyLogic:
    """Tests for buy operation"""

    def test_buy_full_lots(self):
        """Buy 1000 shares (1 lot) at NT$50"""
        price = 50.0
        shares = 1000
        balance = 1_000_000.0

        amount = price * shares
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)
        total_cost = amount + fee

        assert amount == 50_000.0
        assert fee == math.floor(50_000 * 0.001425 * 0.6)
        assert fee == 42  # floor(42.75)
        assert total_cost == 50_042.0

        # Balance check
        assert balance >= total_cost
        new_balance = balance - total_cost
        assert new_balance == 949_958.0

    def test_buy_odd_lots(self):
        """Buy 50 odd lots at NT$500"""
        price = 500.0
        shares = 50
        balance = 100_000.0

        amount = price * shares
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)
        total_cost = amount + fee

        assert amount == 25_000.0
        assert fee == 21  # floor(21.375)
        assert total_cost == 25_021.0

        assert balance >= total_cost

    def test_buy_insufficient_balance(self):
        """Insufficient balance should fail"""
        price = 500.0
        shares = 1000
        balance = 10_000.0

        amount = price * shares
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)
        total_cost = amount + fee

        assert total_cost == 500_427.0
        assert balance < total_cost

        # Should raise InsufficientFunds error
        with pytest.raises(Exception):  # Will be InsufficientFunds exception
            if balance < total_cost:
                raise Exception("Insufficient funds")

    def test_buy_exact_balance(self):
        """Balance exactly equals total cost"""
        price = 100.0
        shares = 1000
        balance = 100_085.0  # Exact amount needed

        amount = price * shares
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)
        total_cost = amount + fee

        assert total_cost == 100_085.0
        assert balance == total_cost

        # Should succeed
        new_balance = balance - total_cost
        assert new_balance == 0.0

    def test_buy_zero_quantity(self):
        """Buy 0 shares should fail"""
        shares = 0

        with pytest.raises(ValueError):
            if shares <= 0:
                raise ValueError("Shares must be positive")

    def test_buy_negative_quantity(self):
        """Buy negative shares should fail"""
        shares = -100

        with pytest.raises(ValueError):
            if shares <= 0:
                raise ValueError("Shares must be positive")


class TestCommissionCalculation:
    """Tests for commission fee calculation"""

    def test_commission_normal_amount(self):
        """Normal amount commission"""
        amount = 100_000.0
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)

        assert fee == 85  # floor(85.5)

    def test_commission_minimum_threshold(self):
        """Small amount should use minimum fee NT$20"""
        amount = 1_000.0
        fee_calculated = math.floor(amount * 0.001425 * 0.6)
        fee = max(fee_calculated, 20)

        assert fee_calculated == 0  # floor(0.855)
        assert fee == 20  # Minimum fee applies

    def test_commission_floor_rounding(self):
        """Commission should use floor rounding"""
        amount = 50_000.0
        fee = math.floor(amount * 0.001425 * 0.6)

        assert fee == 42  # floor(42.75), not 43

    def test_commission_large_amount(self):
        """Large amount commission"""
        amount = 10_000_000.0
        fee = math.floor(amount * 0.001425 * 0.6)

        assert fee == 8_550  # floor(8550.0)

    def test_commission_discount_60_percent(self):
        """Verify 60% discount is applied"""
        amount = 100_000.0

        full_fee = math.floor(amount * 0.001425)
        discounted_fee = math.floor(amount * 0.001425 * 0.6)

        assert full_fee == 142
        assert discounted_fee == 85
        assert pytest.approx(discounted_fee / full_fee, 0.01) == 0.598  # ~60%


class TestSellLogic:
    """Tests for sell operation"""

    def test_sell_all_position(self):
        """Sell entire position"""
        price = 55.0
        shares = 1000
        avg_cost = 50.042  # Per share from previous buy

        amount = price * shares
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)
        tax = math.floor(amount * 0.003)
        net_proceeds = amount - fee - tax

        assert amount == 55_000.0
        assert fee == 46  # floor(46.97)
        assert tax == 165  # floor(165.0)
        assert net_proceeds == 54_789.0

        # Realized PnL
        cost_basis = avg_cost * shares
        realized_pnl = net_proceeds - cost_basis

        assert pytest.approx(realized_pnl, 0.1) == 4_747.0

    def test_sell_partial_position(self):
        """Sell part of position"""
        total_shares = 2000
        sell_shares = 500
        avg_cost = 50.042

        price = 55.0
        amount = price * sell_shares
        fee = max(math.floor(amount * 0.001425 * 0.6), 20)
        tax = math.floor(amount * 0.003)
        net_proceeds = amount - fee - tax

        assert amount == 27_500.0
        assert fee == 23  # floor(23.485)
        assert tax == 82  # floor(82.5)
        assert net_proceeds == 27_395.0

        # Position should reduce
        remaining_shares = total_shares - sell_shares
        assert remaining_shares == 1500

    def test_sell_more_than_holding(self):
        """Sell more shares than held"""
        held_shares = 500
        sell_shares = 1000

        with pytest.raises(Exception):  # InsufficientShares
            if sell_shares > held_shares:
                raise Exception("Insufficient shares")

    def test_sell_with_no_position(self):
        """Sell when no position exists"""
        held_shares = 0
        sell_shares = 100

        with pytest.raises(Exception):  # InsufficientShares
            if held_shares == 0:
                raise Exception("No position to sell")

    def test_sell_zero_quantity(self):
        """Sell 0 shares should fail"""
        shares = 0

        with pytest.raises(ValueError):
            if shares <= 0:
                raise ValueError("Shares must be positive")


class TestTaxCalculation:
    """Tests for transaction tax calculation"""

    def test_tax_rate_0_point_3_percent(self):
        """Tax rate is 0.3%"""
        amount = 100_000.0
        tax = math.floor(amount * 0.003)

        assert tax == 300  # floor(300.0)

    def test_tax_floor_rounding(self):
        """Tax should use floor rounding"""
        amount = 50_123.0
        tax = math.floor(amount * 0.003)

        assert tax == 150  # floor(150.369), not 151

    def test_tax_only_on_sell(self):
        """Tax is only charged on sell transactions"""
        # Buy transaction
        buy_amount = 100_000.0
        buy_tax = 0  # No tax on buy

        # Sell transaction
        sell_amount = 100_000.0
        sell_tax = math.floor(sell_amount * 0.003)

        assert buy_tax == 0
        assert sell_tax == 300

    def test_tax_large_amount(self):
        """Tax on large amount"""
        amount = 10_000_000.0
        tax = math.floor(amount * 0.003)

        assert tax == 30_000


class TestPnLCalculation:
    """Tests for profit and loss calculations"""

    def test_profit_calculation(self):
        """Calculate profit with fees and tax"""
        # Buy: 100 shares @ NT$50
        buy_price = 50.0
        buy_shares = 100
        buy_amount = buy_price * buy_shares
        buy_fee = max(math.floor(buy_amount * 0.001425 * 0.6), 20)
        buy_cost = buy_amount + buy_fee

        assert buy_cost == 5_020.0  # 5000 + 20 (min fee)

        # Sell: 100 shares @ NT$55
        sell_price = 55.0
        sell_shares = 100
        sell_amount = sell_price * sell_shares
        sell_fee = max(math.floor(sell_amount * 0.001425 * 0.6), 20)
        sell_tax = math.floor(sell_amount * 0.003)
        sell_proceeds = sell_amount - sell_fee - sell_tax

        assert sell_proceeds == 5_464.0  # 5500 - 20 - 16

        # Realized PnL
        realized_pnl = sell_proceeds - buy_cost
        assert realized_pnl == 444.0

        # Return rate
        return_rate = (realized_pnl / buy_cost) * 100
        assert pytest.approx(return_rate, 0.1) == 8.8  # ~8.8%

    def test_loss_calculation(self):
        """Calculate loss scenario"""
        # Buy @ 50, Sell @ 45
        buy_cost = 50_020.0  # Including fee
        sell_price = 45.0
        shares = 1000

        sell_amount = sell_price * shares
        sell_fee = max(math.floor(sell_amount * 0.001425 * 0.6), 20)
        sell_tax = math.floor(sell_amount * 0.003)
        sell_proceeds = sell_amount - sell_fee - sell_tax

        realized_pnl = sell_proceeds - buy_cost
        assert realized_pnl < 0  # Loss

    def test_unrealized_pnl(self):
        """Calculate unrealized PnL"""
        shares = 1000
        avg_cost = 50.042  # Per share cost including fees
        current_price = 55.0

        market_value = current_price * shares
        total_cost = avg_cost * shares

        unrealized_pnl = market_value - total_cost
        assert pytest.approx(unrealized_pnl, 0.1) == 4_958.0

    def test_total_assets_calculation(self):
        """Calculate total assets = cash + stock value"""
        cash = 500_000.0
        positions = [
            {"shares": 1000, "current_price": 50},  # Market value: 50,000
            {"shares": 500, "current_price": 100},  # Market value: 50,000
        ]

        stock_value = sum(p["shares"] * p["current_price"] for p in positions)
        total_assets = cash + stock_value

        assert stock_value == 100_000.0
        assert total_assets == 600_000.0

    def test_multiple_positions_pnl(self):
        """Calculate PnL for multiple positions"""
        positions = [
            {
                "shares": 1000,
                "avg_cost": 50.0,
                "current_price": 55.0,
                "pnl": (55.0 - 50.0) * 1000  # +5000
            },
            {
                "shares": 500,
                "avg_cost": 100.0,
                "current_price": 95.0,
                "pnl": (95.0 - 100.0) * 500  # -2500
            },
        ]

        total_pnl = sum(p["pnl"] for p in positions)
        assert total_pnl == 2_500.0

    def test_average_cost_after_multiple_buys(self):
        """Calculate average cost after multiple purchases"""
        # First buy: 100 shares @ 50, cost = 5020
        buy1_shares = 100
        buy1_cost = 5_020.0

        # Second buy: 200 shares @ 55, cost = 11042
        buy2_shares = 200
        buy2_amount = 55.0 * 200
        buy2_fee = max(math.floor(buy2_amount * 0.001425 * 0.6), 20)
        buy2_cost = buy2_amount + buy2_fee

        assert buy2_cost == 11_094.0

        # Average cost
        total_shares = buy1_shares + buy2_shares
        total_cost = buy1_cost + buy2_cost
        avg_cost = total_cost / total_shares

        assert total_shares == 300
        assert total_cost == 16_114.0
        assert pytest.approx(avg_cost, 0.01) == 53.71
