import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { GeneProfilesBlock } from './components/gene-profiles-block.component';
import { Header } from './components/header.component';

test.describe('Gene profiles block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await new Header(page).navLink('Gene Profiles').click();
  });


  test('should display main elements in gene profiles block', async({ page }) => {
    const geneProfilesBlock = new GeneProfilesBlock(page);
    await expect(geneProfilesBlock.root).toBeVisible();
    await expect(geneProfilesBlock.searchInput).toBeVisible();
    await expect(geneProfilesBlock.categoryFilteringButton).toBeVisible();
    await expect(geneProfilesBlock.keybindsIcon).toBeVisible();
    await expect(geneProfilesBlock.geneProfilesTable.root).toBeVisible();
    await expect(geneProfilesBlock.sortingButtons).toHaveCount(19);
  });

  test('should show the keybind tool on keybind icon hover', async({ page }) => {
    const geneProfilesBlock = new GeneProfilesBlock(page);
    await expect(geneProfilesBlock.keybindsTooltip).not.toBeVisible();

    await geneProfilesBlock.keybindsIcon.hover();
    await expect(geneProfilesBlock.keybindsTooltip).toBeVisible();

    await page.mouse.move(30, 30);
    await expect(geneProfilesBlock.keybindsTooltip).not.toBeVisible();
  });
});