import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-inheritancetypes` filter.
export class InheritanceTypes {
  public readonly root: Locator;
  public readonly zygosityFilter: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-inheritancetypes');
    this.zygosityFilter = this.root.locator('gpf-zygosity-filter');
  }

  public button(name: string): Locator {
    return this.root.getByRole('button', { name });
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name);
  }
}
