import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-family-ids` sub-widget of the Family
// filters block.
export class FamilyIds {
  public readonly root: Locator;
  public readonly textarea: Locator;
  public readonly emptyHint: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-family-ids');
    this.textarea = this.root.locator('textarea');
    this.emptyHint = page.getByText('Please insert at least one family id.');
  }

  public async type(text: string): Promise<void> {
    await this.textarea.focus();
    await this.page.keyboard.type(text);
  }

  public async clear(): Promise<void> {
    await this.textarea.clear();
  }
}
