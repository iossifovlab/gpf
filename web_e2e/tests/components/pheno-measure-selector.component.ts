import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-pheno-measure-selector` autocomplete: click
// the search box and pick a measure from the option list that renders at
// page level.
export class PhenoMeasureSelector {
  public readonly root: Locator;
  public readonly searchBox: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-pheno-measure-selector');
    this.searchBox = this.root.locator('#search-box');
  }

  public option(name: string): Locator {
    return this.page.getByText(name);
  }

  public async selectMeasure(name: string): Promise<void> {
    await this.searchBox.click();
    await this.option(name).first().click();
  }
}
