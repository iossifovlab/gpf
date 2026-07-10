import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-variant-types` filter.
export class VariantTypes {
  public readonly root: Locator;
  public readonly zygosityFilter: Locator;
  public readonly selectAtLeastOneError: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-variant-types');
    this.zygosityFilter = this.root.locator('gpf-zygosity-filter');
    this.selectAtLeastOneError = page.getByText('Select at least one.');
  }

  public button(name: string): Locator {
    return this.root.getByRole('button', { name });
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name, { exact: true });
  }
}
