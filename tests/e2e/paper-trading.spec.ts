/**
 * E2E Test: Paper Trading Flow
 * Tests the complete paper trading functionality including buy, sell, and portfolio management
 */
import { test, expect } from '@playwright/test';

test.describe('Paper Trading Operations', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to paper trading page
    await page.goto('/portfolio');
  });

  test('User can buy stock with valid balance', async ({ page }) => {
    // 1. Verify initial balance
    const cashBalance = page.getByTestId('cash-balance');
    await expect(cashBalance).toBeVisible();

    const initialBalance = await cashBalance.textContent();
    const initialBalanceNum = parseFloat(initialBalance!.replace(/,/g, ''));

    // 2. Click buy button
    const buyButton = page.getByTestId('buy-btn');
    await buyButton.click();

    // 3. Fill in buy form
    await page.getByTestId('trade-stock-input').fill('2330');
    await page.getByTestId('trade-quantity').fill('1000'); // 1 lot
    // Price auto-filled from current market price

    // 4. Confirm trade
    await page.getByTestId('confirm-trade-btn').click();

    // 5. Wait for success message
    const successMessage = page.getByTestId('trade-success-message');
    await expect(successMessage).toBeVisible();

    // 6. Verify position appears in portfolio
    const position = page.getByTestId('position-2330');
    await expect(position).toBeVisible();

    // 7. Verify balance decreased
    const newBalance = await cashBalance.textContent();
    const newBalanceNum = parseFloat(newBalance!.replace(/,/g, ''));
    expect(newBalanceNum).toBeLessThan(initialBalanceNum);

    // 8. Verify trade record appears in history
    await page.getByTestId('trade-history-tab').click();
    const latestTrade = page.getByTestId('trade-record-latest');
    await expect(latestTrade).toContainText('買進');
    await expect(latestTrade).toContainText('2330');
  });

  test('User can sell stock from position', async ({ page }) => {
    // Prerequisite: Have a position (this test assumes position exists from previous test or setup)

    // 1. Find position
    const position = page.getByTestId('position-2330');
    await expect(position).toBeVisible();

    // 2. Get current shares
    const sharesElement = position.getByTestId('position-shares');
    const sharesText = await sharesElement.textContent();
    const currentShares = parseInt(sharesText!.replace(/,/g, ''));

    // 3. Click sell button for this position
    const sellButton = position.getByTestId('sell-btn');
    await sellButton.click();

    // 4. Sell partial position (half)
    const sellQuantity = Math.floor(currentShares / 2);
    await page.getByTestId('sell-quantity').fill(sellQuantity.toString());

    // 5. Confirm sell
    await page.getByTestId('confirm-trade-btn').click();

    // 6. Wait for success
    await expect(page.getByTestId('trade-success-message')).toBeVisible();

    // 7. Verify shares decreased
    const newSharesText = await sharesElement.textContent();
    const newShares = parseInt(newSharesText!.replace(/,/g, ''));
    expect(newShares).toBe(currentShares - sellQuantity);

    // 8. Verify realized PnL is displayed
    const realizedPnl = page.getByTestId('trade-realized-pnl');
    await expect(realizedPnl).toBeVisible();
  });

  test('Cannot buy with insufficient balance', async ({ page }) => {
    // 1. Try to buy very expensive stock with large quantity
    await page.getByTestId('buy-btn').click();
    await page.getByTestId('trade-stock-input').fill('2330');
    await page.getByTestId('trade-quantity').fill('10000000'); // Impossibly large

    // 2. Try to confirm
    await page.getByTestId('confirm-trade-btn').click();

    // 3. Should show error message
    const errorMessage = page.getByTestId('error-message');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('餘額不足');
  });

  test('Cannot sell more than held', async ({ page }) => {
    // 1. Find a position
    const position = page.getByTestId('position-2330');
    await expect(position).toBeVisible();

    // 2. Get current shares
    const sharesText = await position.getByTestId('position-shares').textContent();
    const currentShares = parseInt(sharesText!.replace(/,/g, ''));

    // 3. Try to sell more than held
    await position.getByTestId('sell-btn').click();
    await page.getByTestId('sell-quantity').fill((currentShares + 1000).toString());

    // 4. Should show error
    await page.getByTestId('confirm-trade-btn').click();
    const errorMessage = page.getByTestId('error-message');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('持股不足');
  });

  test('Commission and tax are calculated correctly', async ({ page }) => {
    // 1. Initiate buy transaction
    await page.getByTestId('buy-btn').click();
    await page.getByTestId('trade-stock-input').fill('2330');
    await page.getByTestId('trade-quantity').fill('1000');

    // 2. Verify commission calculation preview
    const commission = page.getByTestId('trade-commission-preview');
    await expect(commission).toBeVisible();

    // Commission should be visible and calculated
    const commissionText = await commission.textContent();
    const commissionAmount = parseFloat(commissionText!.replace(/[^0-9.]/g, ''));
    expect(commissionAmount).toBeGreaterThanOrEqual(20); // Min fee is 20

    // 3. Tax should be 0 for buy
    const tax = page.getByTestId('trade-tax-preview');
    const taxText = await tax.textContent();
    expect(taxText).toContain('0');

    // 4. Confirm buy
    await page.getByTestId('confirm-trade-btn').click();
    await expect(page.getByTestId('trade-success-message')).toBeVisible();

    // 5. Now sell - tax should be charged
    const position = page.getByTestId('position-2330');
    await position.getByTestId('sell-btn').click();
    await page.getByTestId('sell-quantity').fill('1000');

    // 6. Verify tax calculation for sell
    const sellTax = page.getByTestId('trade-tax-preview');
    const sellTaxText = await sellTax.textContent();
    const sellTaxAmount = parseFloat(sellTaxText!.replace(/[^0-9.]/g, ''));
    expect(sellTaxAmount).toBeGreaterThan(0); // Tax should be charged on sell
  });
});

test.describe('Portfolio Overview', () => {

  test('Portfolio dashboard shows correct totals', async ({ page }) => {
    await page.goto('/portfolio');

    // 1. Verify 4 main stat cards
    const totalAssets = page.getByTestId('total-assets');
    const stockValue = page.getByTestId('stock-value');
    const cashBalance = page.getByTestId('cash-balance');
    const totalPnl = page.getByTestId('total-pnl');

    await expect(totalAssets).toBeVisible();
    await expect(stockValue).toBeVisible();
    await expect(cashBalance).toBeVisible();
    await expect(totalPnl).toBeVisible();

    // 2. Verify calculation: Total Assets = Cash + Stock Value
    const assetsNum = parseFloat((await totalAssets.textContent())!.replace(/[^0-9.-]/g, ''));
    const stockNum = parseFloat((await stockValue.textContent())!.replace(/[^0-9.-]/g, ''));
    const cashNum = parseFloat((await cashBalance.textContent())!.replace(/[^0-9.-]/g, ''));

    expect(assetsNum).toBeCloseTo(stockNum + cashNum, 1);
  });

  test('Position list shows unrealized PnL', async ({ page }) => {
    await page.goto('/portfolio');

    // Find first position
    const positions = page.getByTestId('positions-list');
    await expect(positions).toBeVisible();

    const firstPosition = positions.locator('[data-testid^="position-"]').first();

    if (await firstPosition.isVisible()) {
      // Check unrealized PnL is displayed
      const unrealizedPnl = firstPosition.getByTestId('unrealized-pnl');
      await expect(unrealizedPnl).toBeVisible();

      // Check percentage is displayed
      const unrealizedPct = firstPosition.getByTestId('unrealized-pnl-pct');
      await expect(unrealizedPct).toBeVisible();
    }
  });

  test('Can reset portfolio to initial state', async ({ page }) => {
    await page.goto('/portfolio');

    // Click reset button
    const resetButton = page.getByTestId('reset-portfolio-btn');
    await resetButton.click();

    // Confirm reset
    const confirmButton = page.getByTestId('confirm-reset-btn');
    await confirmButton.click();

    // Wait for reset
    await page.waitForTimeout(1000);

    // Verify balance is reset to 1,000,000
    const cashBalance = page.getByTestId('cash-balance');
    const balanceText = await cashBalance.textContent();
    expect(balanceText).toContain('1,000,000');

    // Verify no positions
    const positions = page.getByTestId('positions-list');
    const positionCount = await positions.locator('[data-testid^="position-"]').count();
    expect(positionCount).toBe(0);
  });
});
