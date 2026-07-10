import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-family-tags` sub-widget. Tag toggles are
// keyed by tag id (e.g. 'nuclear_family', 'quad_family').
export class FamilyTags {
  public readonly root: Locator;
  public readonly orToggleButton: Locator;
  public readonly clearFiltersButton: Locator;

  public constructor(private readonly page: Page) {
    // Scoped through the family-filters block, matching the original spec.
    this.root = page.locator('gpf-family-filters-block').locator('gpf-family-tags');
    this.orToggleButton = page.locator('.or-toggle-button');
    this.clearFiltersButton = page.locator('#clear-filters-button');
  }

  public tagAdd(tag: string): Locator {
    return this.page.locator(`#tag_${tag}-tag-add`);
  }

  public tagRemove(tag: string): Locator {
    return this.page.locator(`#tag_${tag}-tag-remove`);
  }

  public async addTag(tag: string): Promise<void> {
    await this.tagAdd(tag).click();
  }

  public async removeTag(tag: string): Promise<void> {
    await this.tagRemove(tag).click();
  }

  public async toggleOr(): Promise<void> {
    await this.orToggleButton.click();
  }

  public async clearFilters(): Promise<void> {
    await this.clearFiltersButton.click();
  }
}
