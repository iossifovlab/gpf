import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-regions-block` filter.
export class RegionsBlock {
  public readonly root: Locator;
  public readonly regionsFilterToggle: Locator;
  public readonly filterPanel: Locator;
  public readonly textarea: Locator;
  public readonly emptyError: Locator;
  public readonly errorsAlert: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-regions-block');
    this.regionsFilterToggle = page.locator('#regions-filter');
    this.filterPanel = page.locator('#regions-filter-panel');
    this.textarea = page.locator('gpf-regions-filter textarea');
    this.emptyError = page.getByText('Add at least one region filter.');
    this.errorsAlert = page.locator('gpf-regions-filter').locator('gpf-errors-alert');
  }

  public invalidRegionError(region: string): Locator {
    return this.page.getByText(`Invalid region: ${region}`);
  }
}
