import { Locator, Page } from '@playwright/test';
import { GenesBlock } from '../components/genes-block.component';
import { FamilyFiltersBlock } from '../components/family-filters-block.component';
import { FamilyIds } from '../components/family-ids.component';
import { SelectStudiesModal } from '../components/select-studies-modal.component';
import { PhenoToolMeasure } from '../components/pheno-tool-measure.component';
import { PresentInParent } from '../components/present-in-parent.component';

// Page object for the Phenotype tool, composing the genes block, family
// filters, measure selector and the tool's own query controls.
export class PhenoToolPage {
  public readonly root: Locator;
  public readonly genesBlock: GenesBlock;
  public readonly familyFilters: FamilyFiltersBlock;
  public readonly familyIds: FamilyIds;
  public readonly selectStudiesModal: SelectStudiesModal;
  public readonly measure: PhenoToolMeasure;
  public readonly presentInParent: PresentInParent;

  // Tool blocks.
  public readonly genotypeBlock: Locator;
  public readonly effectTypes: Locator;
  public readonly resultsChart: Locator;
  public readonly measureErrorAlert: Locator;

  // Query controls.
  public readonly reportButton: Locator;
  public readonly downloadButton: Locator;
  public readonly saveQueryDropdownButton: Locator;

  // Family-ids toggle + advanced family filters.
  public readonly familyIdsToggle: Locator;
  public readonly histogram: Locator;
  public readonly fromInput: Locator;
  public readonly toInput: Locator;
  public readonly checkboxList: Locator;
  public readonly categoricalFilter: Locator;
  public readonly dropdownItemSpans: Locator;
  public readonly modalContent: Locator;
  public readonly geneScoresPanelSelect: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-pheno-tool');
    this.genesBlock = new GenesBlock(page);
    this.familyFilters = new FamilyFiltersBlock(page);
    this.familyIds = new FamilyIds(page);
    this.selectStudiesModal = new SelectStudiesModal(page);
    this.measure = new PhenoToolMeasure(page);
    this.presentInParent = new PresentInParent(page);

    this.genotypeBlock = page.locator('gpf-pheno-tool-genotype-block');
    this.effectTypes = page.locator('gpf-pheno-tool-effect-types');
    this.resultsChart = page.locator('gpf-pheno-tool-results-chart');
    this.measureErrorAlert = page.locator('gpf-pheno-tool-measure gpf-errors-alert .alert-danger');

    this.reportButton = page.getByText('Report');
    this.downloadButton = page.getByRole('button', { name: 'Download' });
    this.saveQueryDropdownButton = page.locator('#save-query-dropdown-button');

    this.familyIdsToggle = page.locator('#family-ids');
    this.histogram = page.locator('gpf-histogram');
    this.fromInput = page.locator('#from-input-field');
    this.toInput = page.locator('#to-input-field');
    this.checkboxList = page.locator('gpf-checkbox-list');
    this.categoricalFilter = page.locator('gpf-categorical-filter');
    this.dropdownItemSpans = page.locator('.dropdown-item span');
    this.modalContent = page.locator('.modal-content');
    this.geneScoresPanelSelect = page.locator('#gene-scores-panel select.form-control');
  }

  // Clicks the tool's 'Report' button (scoped to gpf-pheno-tool).
  public async clickReport(): Promise<void> {
    await this.root.getByText('Report').click();
  }

  // An 'All' / 'None' toggle button inside gpf-pheno-tool-effect-types.
  public effectTypesButton(name: string): Locator {
    return this.effectTypes.getByRole('button', { name });
  }

  // An 'Advanced' / 'Gene Sets' / 'Gene Scores' etc. tab by name.
  public tab(name: string): Locator {
    return this.page.getByRole('tab', { name, exact: true });
  }
}
