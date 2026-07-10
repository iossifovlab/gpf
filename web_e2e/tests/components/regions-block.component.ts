import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-regions-block` filter.
export class RegionsBlock {
  public readonly root: Locator;
  public readonly regionsFilterToggle: Locator;
  public readonly textarea: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-regions-block');
    this.regionsFilterToggle = page.locator('#regions-filter');
    this.textarea = page.locator('gpf-regions-filter textarea');
  }
}
