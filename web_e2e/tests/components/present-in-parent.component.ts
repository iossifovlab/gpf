import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-present-in-parent` filter.
export class PresentInParent {
  public readonly root: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-present-in-parent');
  }

  // A radio/checkbox by its accessible label
  // (e.g. 'mother only', 'father only', 'mother and father', 'neither').
  public checkbox(name: string): Locator {
    return this.root.getByLabel(name);
  }

  // The 'ultraRare' rarity radio.
  public ultraRareRadio(): Locator {
    return this.root.getByRole('radio', { name: 'ultraRare' });
  }

  // An 'All' / 'None' toggle button by name.
  public button(name: string): Locator {
    return this.root.locator('button').filter({ hasText: name });
  }
}
