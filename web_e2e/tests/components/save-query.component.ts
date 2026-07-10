import { Locator, Page } from '@playwright/test';

// Component object for the Save / Share query dropdown (`gpf-save-query`)
// and the saved-query rows on the user profile page.
export class SaveQuery {
  public readonly dropdown: Locator;
  public readonly dropdownButton: Locator;
  public readonly linkInput: Locator;
  public readonly copyLinkButton: Locator;
  public readonly nameInput: Locator;
  public readonly descriptionInput: Locator;
  public readonly saveButton: Locator;
  public readonly copiedTooltip: Locator;

  public constructor(private readonly page: Page) {
    this.dropdown = page.locator('#save-query-dropdown');
    this.dropdownButton = page.locator('#save-query-dropdown-button');
    this.linkInput = page.locator('#link-input');
    this.copyLinkButton = page.locator('#copy-link-button');
    this.nameInput = page.locator('gpf-save-query #name');
    this.descriptionInput = page.locator('gpf-save-query #description');
    this.saveButton = page.locator('gpf-save-query #save-button');
    this.copiedTooltip = page.locator('ngb-tooltip-window');
  }

  // The actions cell for a saved query on the user profile page.
  public savedQueryCell(name: string): Locator {
    return this.page.locator(`div[id="query-${name}-actions-cell"]`);
  }

  // The load button inside a saved-query actions cell.
  public loadButton(name: string): Locator {
    return this.savedQueryCell(name).locator('#load-button');
  }

  // The delete button inside a saved-query actions cell.
  public deleteButton(name: string): Locator {
    return this.savedQueryCell(name).locator('#delete-button');
  }
}
