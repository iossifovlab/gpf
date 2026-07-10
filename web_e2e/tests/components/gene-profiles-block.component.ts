import { Locator, Page } from '@playwright/test';
import { GeneProfilesTable } from './gene-profiles-table.component';

// Component object for the `gpf-gene-profiles-block` (search input,
// category filtering, keybinds) wrapping the gene-profiles table.
export class GeneProfilesBlock {
  public readonly root: Locator;
  public readonly searchInput: Locator;
  public readonly categoryFilteringButton: Locator;
  public readonly keybindsIcon: Locator;
  public readonly keybindsTooltip: Locator;
  public readonly table: Locator;
  public readonly sortingButtons: Locator;
  public readonly geneProfilesTable: GeneProfilesTable;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-profiles-block');
    this.searchInput = page.locator('#gene-search-input');
    this.categoryFilteringButton = page.locator('#category-filtering-button');
    this.keybindsIcon = page.locator('#keybinds-icon');
    this.keybindsTooltip = page.locator('.keybinds-tooltip');
    this.table = page.locator('gpf-gene-profiles-table');
    this.sortingButtons = page.locator('gpf-sorting-buttons');
    this.geneProfilesTable = new GeneProfilesTable(page);
  }
}
