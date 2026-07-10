import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-pedigree-selector` filter and its
// dropdown menu.
export class PedigreeSelector {
  public readonly root: Locator;
  public readonly dropdownButton: Locator;
  public readonly affectedStatusLink: Locator;
  public readonly noneButton: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-pedigree-selector');
    this.dropdownButton = page.locator('#pedigree-dropdown-menu-button');
    this.affectedStatusLink = this.root.getByRole('link', { name: 'Affected Status' });
    this.noneButton = this.root.getByRole('button', { name: 'None' });
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name, { exact: true });
  }

  public async openAffectedStatus(): Promise<void> {
    await this.dropdownButton.click();
    await this.affectedStatusLink.click();
  }
}
