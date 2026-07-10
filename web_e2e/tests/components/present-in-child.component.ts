import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-present-in-child` filter.
export class PresentInChild {
  public readonly root: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-present-in-child');
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name, { exact: true });
  }
}
