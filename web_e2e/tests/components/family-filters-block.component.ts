import { Locator, Page } from '@playwright/test';
import { FamilyIds } from './family-ids.component';
import { FamilyTags } from './family-tags.component';
import { PersonFilters } from './person-filters.component';

// Component object for the `gpf-family-filters-block` widget: the tab bar
// (All / Family Ids / Family Tags / Pheno Measures / Advanced) plus the
// nested sub-components.
export class FamilyFiltersBlock {
  public readonly root: Locator;
  public readonly familyIds: FamilyIds;
  public readonly familyTags: FamilyTags;
  public readonly phenoMeasures: PersonFilters;

  // tabs
  public readonly familyIdsTab: Locator;
  public readonly familyTagsTab: Locator;
  public readonly phenoMeasuresTab: Locator;
  public readonly advancedTab: Locator;
  public readonly phenoMeasuresRoleTab: Locator;

  // toggles / panels
  public readonly familyIdsToggle: Locator;
  public readonly phenoMeasuresToggle: Locator;
  public readonly familyIdsPanel: Locator;
  public readonly phenoFiltersPanel: Locator;

  // advanced (multi-continuous filter)
  public readonly multiContinuousFilter: Locator;
  public readonly selectContinuousFilterHint: Locator;
  public readonly advancedSearchBox: Locator;
  public readonly histogram: Locator;
  public readonly measuresSearchInput: Locator;
  public readonly measuresTextbox: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-family-filters-block');
    this.familyIds = new FamilyIds(page);
    this.familyTags = new FamilyTags(page);
    this.phenoMeasures = new PersonFilters(page);

    this.familyIdsTab = this.root.getByText('Family Ids');
    this.familyTagsTab = this.root.getByText('Family Tags');
    this.phenoMeasuresTab = this.root.getByText('Pheno Measures');
    this.advancedTab = this.root.getByRole('tab', { name: 'Advanced', exact: true });
    this.phenoMeasuresRoleTab = this.root.getByRole('tab', { name: 'Pheno Measures', exact: true });

    this.familyIdsToggle = page.locator('#family-ids');
    this.phenoMeasuresToggle = this.root.locator('#phenoMeasures');
    this.familyIdsPanel = page.locator('#family-ids-panel');
    this.phenoFiltersPanel = page.locator('#pheno-filters-panel');

    this.multiContinuousFilter = this.root.locator('gpf-multi-continuous-filter');
    this.selectContinuousFilterHint = page.getByText('Select at least one continuous filter.');
    this.advancedSearchBox = this.root.locator('#search-box');
    this.histogram = page.locator('gpf-histogram');
    this.measuresSearchInput = this.root.getByPlaceholder('Select or start typing to');
    this.measuresTextbox = this.root.getByRole('textbox', { name: 'Select or start typing to' });
  }

  public advancedMeasureOption(name: string): Locator {
    return this.page.locator('.dropdown-item span', { hasText: name });
  }

  public async openFamilyIds(): Promise<void> {
    await this.familyIdsToggle.click();
  }

  public async openFamilyIdsTab(): Promise<void> {
    await this.familyIdsTab.click();
  }

  public async openFamilyTagsTab(): Promise<void> {
    await this.familyTagsTab.click();
  }

  public async openPhenoMeasuresTab(): Promise<void> {
    await this.phenoMeasuresTab.click();
  }

  public async openPhenoMeasuresToggle(): Promise<void> {
    await this.phenoMeasuresToggle.click();
  }

  public async openAdvancedTab(): Promise<void> {
    await this.advancedTab.click();
  }

  public async openAllTab(): Promise<void> {
    await this.root.getByText('All').click();
  }
}
