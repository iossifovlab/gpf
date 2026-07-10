import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-effect-types` filter. Preset buttons
// (All / None / LGDs / ...) are addressed by name; individual effect
// checkboxes by their label.
export class EffectTypes {
  public readonly root: Locator;
  public readonly zygosityFilter: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-effect-types');
    this.zygosityFilter = this.root.locator('gpf-zygosity-filter');
  }

  public button(name: string): Locator {
    return this.root.getByRole('button', { name });
  }

  public label(name: string): Locator {
    return this.root.getByLabel(name);
  }

  public async clickButton(name: string): Promise<void> {
    await this.button(name).click();
  }

  public async clickLabel(name: string): Promise<void> {
    await this.label(name).click();
  }
}
