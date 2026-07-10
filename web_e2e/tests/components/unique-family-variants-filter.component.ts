import { Locator, Page } from '@playwright/test';

// Component object for the unique family variants filter.
export class UniqueFamilyVariantsFilter {
  public readonly block: Locator;
  public readonly checkbox: Locator;
  public readonly variantsCountSpan: Locator;

  public constructor(private readonly page: Page) {
    this.block = page.locator('#unique-family-variants-block');
    this.checkbox = page.locator('#unique-family-variants-checkbox');
    this.variantsCountSpan = page.locator('#variants-count-span');
  }
}
