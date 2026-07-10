import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gene-browser` view.
export class GeneBrowser {
  public readonly root: Locator;
  public readonly searchBox: Locator;
  public readonly goButton: Locator;
  public readonly genePlot: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-browser');
    this.searchBox = this.root.locator('input#search-box');
    this.goButton = page.getByText('Go');
    this.genePlot = page.locator('gpf-gene-plot');
  }

  // Searches for a gene and waits for its plot to render.
  public async searchGene(symbol: string): Promise<void> {
    await this.searchBox.fill(symbol);
    await this.goButton.click();
  }
}
