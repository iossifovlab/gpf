import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-pheno-tool-measure` widget (measure
// search box, dropdown, clear button and normalization checkboxes).
export class PhenoToolMeasure {
  public readonly root: Locator;
  public readonly searchBox: Locator;
  public readonly measuresDropdown: Locator;
  public readonly clearMeasureButton: Locator;
  public readonly pleaseSelectMeasureError: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-pheno-tool-measure');
    this.searchBox = this.root.locator('#search-box');
    this.measuresDropdown = page.locator('.measures-dropdown');
    this.clearMeasureButton = page.locator('#clear-measure-button');
    this.pleaseSelectMeasureError = page.getByText('Please select a measure.');
  }

  // A normalization checkbox by its label (e.g. 'Age', 'Non verbal IQ').
  public normalizationCheckbox(name: string): Locator {
    return this.page.getByLabel(name);
  }

  // A measure option inside the dropdown by its full name.
  public measureOption(name: string): Locator {
    return this.measuresDropdown.getByText(name);
  }

  // Opens the dropdown and selects a measure by name.
  public async selectMeasure(name: string): Promise<void> {
    await this.searchBox.click();
    await this.page.getByText(name).first().click();
  }
}
