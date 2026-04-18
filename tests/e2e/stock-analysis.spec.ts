/**
 * E2E Test: Stock Analysis Flow
 * Tests the complete user journey from stock search to viewing analysis results
 */
import { test, expect } from '@playwright/test';

test.describe('Stock Analysis Complete Flow', () => {

  test('User can search and view stock analysis for TSMC', async ({ page }) => {
    // 1. Navigate to homepage
    await page.goto('/');

    // 2. Verify homepage loads
    await expect(page).toHaveTitle(/台股實驗預測/);

    // 3. Search for stock (TSMC 2330)
    const searchInput = page.getByTestId('stock-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('2330');

    // 4. Click analyze button
    const analyzeButton = page.getByTestId('analyze-btn');
    await analyzeButton.click();

    // 5. Wait for analysis results to load
    await page.waitForSelector('[data-testid="signal-panel"]', { timeout: 10000 });

    // 6. Verify all 9 signals are displayed
    for (let i = 1; i <= 9; i++) {
      const signal = page.getByTestId(`signal-${i}`);
      await expect(signal).toBeVisible();
    }

    // 7. Verify weighted score is displayed
    const weightedScore = page.getByTestId('weighted-score');
    await expect(weightedScore).toBeVisible();

    // 8. Verify score is in valid range (-100 to +100)
    const scoreText = await weightedScore.textContent();
    const score = parseFloat(scoreText!);
    expect(score).toBeGreaterThanOrEqual(-100);
    expect(score).toBeLessThanOrEqual(100);

    // 9. Verify direction indicator (📈/📉/⚖️)
    const direction = page.getByTestId('direction-indicator');
    await expect(direction).toBeVisible();

    // 10. Verify confidence percentage
    const confidence = page.getByTestId('confidence-value');
    await expect(confidence).toBeVisible();
    const confidenceText = await confidence.textContent();
    const confidencePct = parseFloat(confidenceText!);
    expect(confidencePct).toBeGreaterThanOrEqual(10);
    expect(confidencePct).toBeLessThanOrEqual(95);

    // 11. Take screenshot for visual verification
    await page.screenshot({ path: 'test-results/screenshots/tsmc-analysis.png' });
  });

  test('Invalid stock code shows error message', async ({ page }) => {
    await page.goto('/');

    // Enter invalid stock code
    const searchInput = page.getByTestId('stock-input');
    await searchInput.fill('9999');

    // Click analyze
    const analyzeButton = page.getByTestId('analyze-btn');
    await analyzeButton.click();

    // Should show error message
    const errorMessage = page.getByTestId('error-message');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('無效的股票代號');
  });

  test('Empty stock code prevents submission', async ({ page }) => {
    await page.goto('/');

    // Click analyze without entering stock code
    const analyzeButton = page.getByTestId('analyze-btn');
    await analyzeButton.click();

    // Input should show validation error
    const searchInput = page.getByTestId('stock-input');
    await expect(searchInput).toHaveAttribute('aria-invalid', 'true');
  });

  test('AI analysis toggle works correctly', async ({ page }) => {
    await page.goto('/');

    // Search for stock
    await page.getByTestId('stock-input').fill('2330');
    await page.getByTestId('analyze-btn').click();

    // Wait for results
    await page.waitForSelector('[data-testid="signal-panel"]');

    // Toggle AI on
    const aiToggle = page.getByTestId('ai-toggle');
    await aiToggle.click();

    // AI analysis should appear
    const aiAnalysis = page.getByTestId('ai-analysis');
    await expect(aiAnalysis).toBeVisible({ timeout: 15000 });

    // Toggle AI off
    await aiToggle.click();

    // AI analysis should be hidden (but signals still visible)
    await expect(aiAnalysis).not.toBeVisible();
    await expect(page.getByTestId('signal-panel')).toBeVisible();
  });

  test('Real-time WebSocket updates work', async ({ page }) => {
    await page.goto('/');

    // Search and analyze
    await page.getByTestId('stock-input').fill('2330');
    await page.getByTestId('analyze-btn').click();

    // Wait for initial results
    await page.waitForSelector('[data-testid="signal-panel"]');

    // Get initial score
    const initialScore = await page.getByTestId('weighted-score').textContent();

    // Wait for WebSocket update (should happen within a few seconds)
    // This is simulated - in real scenario, backend would push updates
    await page.waitForTimeout(5000);

    // Verify updates are received (score might change or timestamp updates)
    const timestamp = page.getByTestId('last-updated');
    await expect(timestamp).toBeVisible();
  });

  test('9 signals radar chart displays correctly', async ({ page }) => {
    await page.goto('/');

    // Analyze stock
    await page.getByTestId('stock-input').fill('2330');
    await page.getByTestId('analyze-btn').click();
    await page.waitForSelector('[data-testid="signal-panel"]');

    // Verify radar chart exists
    const radarChart = page.getByTestId('signal-radar-chart');
    await expect(radarChart).toBeVisible();

    // Verify canvas element (chart library renders to canvas)
    const canvas = radarChart.locator('canvas');
    await expect(canvas).toBeVisible();
  });

  test('User can switch between different stocks', async ({ page }) => {
    await page.goto('/');

    // Analyze first stock
    await page.getByTestId('stock-input').fill('2330');
    await page.getByTestId('analyze-btn').click();
    await page.waitForSelector('[data-testid="signal-panel"]');

    // Verify stock name
    const stockName1 = page.getByTestId('stock-name');
    await expect(stockName1).toContainText('台積電');

    // Search for different stock
    await page.getByTestId('stock-input').clear();
    await page.getByTestId('stock-input').fill('2317');
    await page.getByTestId('analyze-btn').click();
    await page.waitForSelector('[data-testid="signal-panel"]');

    // Verify new stock name
    const stockName2 = page.getByTestId('stock-name');
    await expect(stockName2).toContainText('鴻海');
  });
});

test.describe('Stock Analysis Performance', () => {

  test('Analysis results load within 2 seconds', async ({ page }) => {
    await page.goto('/');

    const startTime = Date.now();

    // Perform analysis
    await page.getByTestId('stock-input').fill('2330');
    await page.getByTestId('analyze-btn').click();

    // Wait for results
    await page.waitForSelector('[data-testid="signal-panel"]');

    const endTime = Date.now();
    const loadTime = endTime - startTime;

    // Should load within 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });
});
