import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-pedigree-selector` filter and its
// dropdown menu.
export class PedigreeSelector {
  public readonly root: Locator;
  public readonly dropdownButton: Locator;
  public readonly affectedStatusLink: Locator;
  public readonly noneButton: Locator;
  public readonly allButton: Locator;
  public readonly checkboxes: Locator;
  public readonly selectAtLeastOneError: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-pedigree-selector');
    this.dropdownButton = page.locator('#pedigree-dropdown-menu-button');
    this.affectedStatusLink = this.root.getByRole('link', { name: 'Affected Status' });
    this.noneButton = this.root.getByText('None');
    this.allButton = this.root.getByText('All');
    this.checkboxes = this.root.locator('.checkbox');
    this.selectAtLeastOneError = this.root.getByText('Select at least one.');
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name, { exact: true });
  }

  public async openAffectedStatus(): Promise<void> {
    await this.dropdownButton.click();
    await this.affectedStatusLink.click();
  }

  // Opens the dropdown and selects a category (e.g. 'Role', 'Phenotype').
  public async openCategory(name: string): Promise<void> {
    await this.dropdownButton.click();
    await this.page.getByRole('link', { name, exact: true }).click();
  }
}
