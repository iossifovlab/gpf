import { Locator, Page } from '@playwright/test';

// Component object for the per-filter zygosity sub-filters. Each carrier
// filter (pedigreeSelector / presentInChild / presentInParent /
// carrierGender) renders its own `#<name>-zygosity-filter` block with
// homozygous / heterozygous checkboxes.
export class ZygosityFilters {
  private readonly page: Page;

  public constructor(page: Page) {
    this.page = page;
  }

  public filter(name: string): Locator {
    return this.page.locator(`#${name}-zygosity-filter`);
  }

  public checkbox(name: string, label: string): Locator {
    return this.filter(name).getByLabel(label);
  }

  public selectAtLeastOneError(name: string): Locator {
    return this.filter(name).getByText('Select at least one zygosity.');
  }
}
