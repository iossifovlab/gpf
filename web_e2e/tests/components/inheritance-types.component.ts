import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-inheritancetypes` filter.
export class InheritanceTypes {
  public readonly root: Locator;
  public readonly zygosityFilter: Locator;
  public readonly checkboxes: Locator;
  public readonly selectAtLeastOneError: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-inheritancetypes');
    this.zygosityFilter = this.root.locator('gpf-zygosity-filter');
    this.checkboxes = this.root.locator('.checkbox');
    this.selectAtLeastOneError = this.root.getByText('Select at least one.');
  }

  public button(name: string): Locator {
    return this.root.getByRole('button', { name });
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name, { exact: true });
  }
}
