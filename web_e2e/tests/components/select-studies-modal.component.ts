import { Locator, Page } from '@playwright/test';

// Component object for the "Select studies" modal opened from the Denovo
// gene-set collection. Study-scoped controls are exposed as parameterized
// methods (keyed by study id) rather than one locator per fixture study.
export class SelectStudiesModal {
  public readonly openButton: Locator;
  public readonly content: Locator;
  public readonly hierarchy: Locator;
  public readonly filters: Locator;
  public readonly modalFilterList: Locator;
  public readonly selectedFilterList: Locator;
  public readonly affectedStatusLabel: Locator;

  public constructor(private readonly page: Page) {
    this.openButton = page.getByRole('button', { name: 'Select studies' });
    this.content = page.locator('.modal-content');
    this.hierarchy = page.locator('#hierarchy');
    this.filters = page.locator('#filters');
    this.modalFilterList = page.locator('#modal-filter-list');
    this.selectedFilterList = page.locator('#selected-filter-list');
    this.affectedStatusLabel = page.getByText('Affected Status:');
  }

  public datasetNode(id: string): Locator {
    return this.page.locator(`#dataset-${id}`);
  }

  public expandToggle(id: string): Locator {
    return this.page.locator(`#expand-${id}`);
  }

  public affectedCheckbox(study: string): Locator {
    return this.page.locator(`#${study}-checkbox-affected`);
  }

  public unaffectedCheckbox(study: string): Locator {
    return this.page.locator(`#${study}-checkbox-unaffected`);
  }

  public modalFilterItem(text: string): Locator {
    return this.modalFilterList.getByText(text);
  }

  public removeFilterButton(text: string): Locator {
    return this.page.locator(`[id="remove-${text}"]`);
  }

  public async open(): Promise<void> {
    await this.openButton.click();
  }
}
