import { Locator, Page } from '@playwright/test';

// Component object for the categorical histogram with its three selection
// modes (range / click / dropdown). Bars are addressed by rect id, dropdown
// values by their label text.
export class CategoricalHistogram {
  public readonly root: Locator;
  public readonly modeButton: Locator;
  public readonly menuContent: Locator;
  public readonly rangeSelectorLines: Locator;
  public readonly searchBox: Locator;
  public readonly valuesList: Locator;
  public readonly valueWrapper: Locator;
  public readonly removeValue: Locator;
  public readonly pleaseSelectValueHint: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-categorical-histogram');
    this.modeButton = page.getByRole('button', { name: 'Mode' });
    this.menuContent = page.locator('.mat-mdc-menu-content');
    this.rangeSelectorLines = page.locator('[gpf-histogram-range-selector-line]');
    this.searchBox = page.locator('#search-box');
    this.valuesList = page.locator('#values-list');
    this.valueWrapper = page.locator('.value-wrapper');
    this.removeValue = page.locator('.remove-value');
    this.pleaseSelectValueHint = page.getByText('Please select at least one value.');
  }

  public modeMenuItem(name: string): Locator {
    return this.page.getByRole('menuitem', { name });
  }

  public bar(id: string): Locator {
    return this.page.locator(`rect[id="${id}"]`);
  }

  public matOption(text: string): Locator {
    return this.page.locator('mat-option').getByText(text);
  }

  public matOptionHasText(text: string): Locator {
    return this.page.locator(`mat-option:has-text("${text}")`);
  }

  public async openMode(): Promise<void> {
    await this.modeButton.click();
  }

  public async selectMode(name: string): Promise<void> {
    await this.modeButton.click();
    await this.modeMenuItem(name).click();
  }
}
