import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Gene profiles block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });


  test('should display main elements in gene profiles block', async({ page }) => {
    await expect(page.locator('gpf-gene-profiles-block')).toBeVisible();
    await expect(page.locator('#gene-search-input')).toBeVisible();
    await expect(page.locator('#category-filtering-button')).toBeVisible();
    await expect(page.locator('#keybinds-icon')).toBeVisible();
    await expect(page.locator('gpf-gene-profiles-table')).toBeVisible();
    await expect(page.locator('gpf-sorting-buttons')).toHaveCount(19);
  });

  test('should show the keybind tool on keybind icon hover', async({ page }) => {
    await expect(page.locator('.keybinds-tooltip')).not.toBeVisible();

    await page.locator('#keybinds-icon').hover();
    await expect(page.locator('.keybinds-tooltip')).toBeVisible();

    await page.mouse.move(30, 30);
    await expect(page.locator('.keybinds-tooltip')).not.toBeVisible();
  });
});