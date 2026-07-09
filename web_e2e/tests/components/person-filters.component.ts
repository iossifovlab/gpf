import { Locator, Page } from '@playwright/test';

// Component object for the pheno-measures person-filters widget: the
// measures search dropdown, the list of `gpf-person-filter` histograms,
// the role selector and histogram mode controls. Locators are page-scoped
// because the underlying DOM (`.measures-dropdown`, `gpf-person-filter`,
// `gpf-role-selector`) is rendered at page level, matching the specs.
export class PersonFilters {
  public readonly measuresSearchInput: Locator;
  public readonly measuresDropdown: Locator;
  public readonly measuresDropdownContainer: Locator;
  public readonly personFilters: Locator;
  public readonly personFilterTitles: Locator;
  public readonly personFiltersSelector: Locator;
  public readonly selectMeasureHint: Locator;
  public readonly pleaseSelectValueHint: Locator;
  public readonly rangeStartBelowMinError: Locator;
  public readonly roleSelector: Locator;
  public readonly roleSearchBox: Locator;
  public readonly roleOptions: Locator;
  public readonly roleWrappers: Locator;
  public readonly rolesList: Locator;
  public readonly modeButton: Locator;
  public readonly sumOfBarsLabel: Locator;
  public readonly histogramFromLabel: Locator;
  public readonly histogramToLabel: Locator;

  public constructor(private readonly page: Page) {
    this.measuresSearchInput = page.getByPlaceholder('Select or start typing to');
    this.measuresDropdown = page.locator('.measures-dropdown');
    this.measuresDropdownContainer = page.locator('#measures-dropdown');
    this.personFilters = page.locator('gpf-person-filter');
    this.personFilterTitles = page.locator('gpf-person-filter .title-wrapper');
    this.personFiltersSelector = page.locator('gpf-person-filters-selector');
    this.selectMeasureHint = page.getByText('Select a measure.');
    this.pleaseSelectValueHint = page.getByText('Please select at least one value.');
    this.rangeStartBelowMinError = page.getByText('Range start should be more than or equal to domain min.');
    this.roleSelector = page.locator('gpf-role-selector');
    this.roleSearchBox = page.locator('gpf-role-selector #search-box');
    this.roleOptions = page.getByRole('option');
    this.roleWrappers = page.locator('.role-wrapper');
    this.rolesList = page.locator('#roles-list');
    this.modeButton = page.getByRole('button', { name: 'Mode' });
    this.sumOfBarsLabel = page.locator('#sumOfBarsLabel');
    this.histogramFromLabel = page.locator('.histogram-from label');
    this.histogramToLabel = page.locator('.histogram-to label');
  }

  public measureOption(name: string): Locator {
    return this.measuresDropdown.getByText(name);
  }

  public personFilterFor(measure: string): Locator {
    return this.personFilters.filter({ hasText: measure });
  }

  public personFilterTitle(index: number): Locator {
    return this.personFilterTitles.nth(index);
  }

  public removeButton(measure: string): Locator {
    return this.page.locator(`[id="${measure}-remove-button"]`);
  }

  public fromInput(measure: string): Locator {
    return this.personFilterFor(measure).locator('#from-input-field');
  }

  public toInput(measure: string): Locator {
    return this.personFilterFor(measure).locator('#to-input-field');
  }

  public startInput(measure: string): Locator {
    return this.personFilterFor(measure).getByPlaceholder('start');
  }

  public roleOption(role: string): Locator {
    return this.page.getByRole('option', { name: role });
  }

  public modeMenuItem(name: string): Locator {
    return this.page.getByRole('menuitem', { name });
  }

  public histogramBar(id: string): Locator {
    return this.page.locator(`rect[id="${id}"]`);
  }

  public async selectMeasure(name: string): Promise<void> {
    await this.measuresSearchInput.click();
    await this.measureOption(name).click();
  }

  public async selectMode(name: string): Promise<void> {
    await this.modeButton.click();
    await this.modeMenuItem(name).click();
  }

  // Opens the role dropdown for a measure and picks a role, waiting for
  // the histogram + role-list responses the UI fires.
  public async selectRole(measure: string, role: string): Promise<void> {
    await this.personFilterFor(measure).getByPlaceholder('Select role').click();

    const histogramResponse = this.page.waitForResponse(
      resp => resp.url().includes('/api/v3/measures/histogram-beta') && resp.status() === 200
    );
    const roleListResponse = this.page.waitForResponse(
      resp => resp.url().includes('/api/v3/measures/role-list') && resp.status() === 200
    );

    await this.page.locator('mat-option').getByText(role).click();
    await histogramResponse;
    await roleListResponse;

    await this.page.waitForSelector('gpf-person-filter .role-wrapper');
  }

  public async removeRole(measure: string, role: string): Promise<void> {
    const histogramResponse = this.page.waitForResponse(
      resp => resp.url().includes('/api/v3/measures/histogram-beta') && resp.status() === 200
    );
    const roleListResponse = this.page.waitForResponse(
      resp => resp.url().includes('/api/v3/measures/role-list') && resp.status() === 200
    );

    await this.personFilterFor(measure).locator(`#remove-${role}`).click();

    await histogramResponse;
    await roleListResponse;
  }
}
