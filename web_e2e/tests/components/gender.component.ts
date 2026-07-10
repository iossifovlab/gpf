import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gender` filter.
export class Gender {
  public readonly root: Locator;
  public readonly noneButton: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gender');
    this.noneButton = this.root.getByRole('button', { name: 'None' });
  }

  public genderIcon(gender: string): Locator {
    return this.page.locator(`[class="gender-icon ${gender}"]`);
  }
}
