import { Locator, Page } from '@playwright/test';

// Minimal component object for the `gpf-person-filters-block` widget. Only
// the surface used by family-filters-block.spec.ts is modelled here; a full
// component object can grow when person-filters-block gets its own spec
// converted.
export class PersonFiltersBlock {
  public readonly root: Locator;
  public readonly phenoMeasuresTab: Locator;
  public readonly measuresTextbox: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-person-filters-block');
    this.phenoMeasuresTab = this.root.getByText('Pheno Measures');
    this.measuresTextbox = this.root.getByRole('textbox', { name: 'Select or start typing to' });
  }

  public async openPhenoMeasuresTab(): Promise<void> {
    await this.phenoMeasuresTab.click();
  }
}
