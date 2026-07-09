import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gene-symbols` block nested inside the
// Genes block. Exposes named locators + actions so specs never touch raw
// selector strings. Assertions stay in the specs.
export class GeneSymbols {
  public readonly root: Locator;
  public readonly textbox: Locator;
  public readonly errorsAlert: Locator;
  public readonly emptyHint: Locator;
  public readonly caseSensitiveNote: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-symbols');
    this.textbox = this.root.getByRole('textbox');
    this.errorsAlert = this.root.locator('gpf-errors-alert');
    this.emptyHint = page.getByText('Please insert at least one gene symbol.');
    this.caseSensitiveNote = page.getByText('* Gene symbols are case-sensitive');
  }

  public invalidGenes(genes: string): Locator {
    return this.page.getByText(`Invalid genes: ${genes}`);
  }

  public async type(text: string): Promise<void> {
    await this.textbox.pressSequentially(text);
  }

  public async clear(): Promise<void> {
    await this.textbox.clear();
  }
}
