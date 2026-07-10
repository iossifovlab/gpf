import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gender` filter.
export class Gender {
  public readonly root: Locator;
  public readonly noneButton: Locator;
  public readonly allButton: Locator;
  public readonly selectAtLeastOneError: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gender');
    this.noneButton = this.root.getByRole('button', { name: 'None' });
    this.allButton = this.root.getByRole('button', { name: 'All' });
    this.selectAtLeastOneError = this.root.getByText('Select at least one.');
  }

  public genderIcon(gender: string): Locator {
    return this.page.locator(`[class="gender-icon ${gender}"]`);
  }

  // The child-gender checkbox inside the block (by gender class).
  public checkbox(gender: string): Locator {
    return this.root.locator(`.${gender}`);
  }
}
