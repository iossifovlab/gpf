import { Locator, Page } from '@playwright/test';
import { GenesBlock } from '../components/genes-block.component';
import { FamilyFiltersBlock } from '../components/family-filters-block.component';
import { PersonFiltersBlock } from '../components/person-filters-block.component';
import { GenomicScoresBlock } from '../components/genomic-scores-block.component';
import { GenotypeBlock } from '../components/genotype-block.component';
import { RegionsBlock } from '../components/regions-block.component';
import { EffectTypes } from '../components/effect-types.component';

// Page object for the Genotype browser route. Composes the block-level
// component objects and owns the shared query controls (Table Preview /
// Share-save / Download buttons, variant count, preview table) that many
// specs reuse.
export class GenotypeBrowserPage {
  public readonly genes: GenesBlock;
  public readonly familyFilters: FamilyFiltersBlock;
  public readonly personFilters: PersonFiltersBlock;
  public readonly genomicScores: GenomicScoresBlock;
  public readonly genotypeBlock: GenotypeBlock;
  public readonly regions: RegionsBlock;
  public readonly effectTypes: EffectTypes;

  public readonly root: Locator;
  public readonly tablePreviewButton: Locator;
  public readonly shareSaveButton: Locator;
  public readonly downloadButton: Locator;
  public readonly variantsCount: Locator;
  public readonly variantsCountSpan: Locator;
  public readonly saveQueryDropdown: Locator;
  public readonly saveQueryDropdownButton: Locator;
  public readonly linkInput: Locator;
  public readonly previewTable: Locator;
  // id-based variants of the query-control buttons used by some specs
  public readonly tablePreviewButtonId: Locator;
  public readonly downloadButtonId: Locator;

  // preview-result / table locators
  public readonly uniqueFamilyVariantsFilter: Locator;
  public readonly sortChild: Locator;
  public readonly detailsModal: Locator;
  public readonly detailsHeaders: Locator;
  public readonly detailsGrid: Locator;
  public readonly overlay: Locator;
  public readonly showDetails: Locator;
  public readonly tableViewCell: Locator;

  public constructor(private readonly page: Page) {
    this.genes = new GenesBlock(page);
    this.familyFilters = new FamilyFiltersBlock(page);
    this.personFilters = new PersonFiltersBlock(page);
    this.genomicScores = new GenomicScoresBlock(page);
    this.genotypeBlock = new GenotypeBlock(page);
    this.regions = new RegionsBlock(page);
    this.effectTypes = new EffectTypes(page);

    this.root = page.locator('gpf-genotype-browser');
    this.tablePreviewButton = page.getByRole('button', { name: 'Table Preview' });
    this.shareSaveButton = page.getByRole('button', { name: 'Share/save query' });
    this.downloadButton = page.getByRole('button', { name: 'Download' });
    this.variantsCount = page.locator('#variants-count-span');
    this.variantsCountSpan = page.locator('#variants-count-span > span');
    this.saveQueryDropdown = page.locator('#save-query-dropdown');
    this.saveQueryDropdownButton = page.locator('#save-query-dropdown-button');
    this.linkInput = page.locator('#link-input');
    this.previewTable = page.locator('gpf-genotype-preview-table');
    this.tablePreviewButtonId = page.locator('#table-preview-button');
    this.downloadButtonId = page.locator('#download-button');

    this.uniqueFamilyVariantsFilter = page.locator('gpf-unique-family-variants-filter');
    this.sortChild = page.locator('#sort-child');
    this.detailsModal = page.locator('.modal-content');
    this.detailsHeaders = page.locator('.modal-content > .details-header');
    this.detailsGrid = page.locator('.modal-content > .grid-container');
    this.overlay = page.locator('.overlay');
    this.showDetails = page.getByText('Show details');
    this.tableViewCell = page.locator('gpf-table-view-cell:nth-child(6) > div');
  }

  // A variant location link in the preview table (matched by its text).
  public variantLink(pattern: RegExp): Locator {
    return this.page.locator('a').filter({ hasText: pattern });
  }

  public async waitForLoaded(): Promise<void> {
    await this.root.waitFor();
  }

  public async runTablePreview(): Promise<void> {
    await this.tablePreviewButton.click();
  }

  // Opens the share/save dropdown and returns the shareable query URL.
  // Waits for the dropdown to render before reading the link, matching
  // the original specs' ordering.
  public async getShareLink(): Promise<string> {
    await this.shareSaveButton.click();
    await this.saveQueryDropdown.waitFor();
    return this.linkInput.inputValue();
  }

  // Switches the active tool via the top-of-page text link (e.g.
  // 'Phenotype browser', 'Genotype browser').
  public async switchToTool(label: string): Promise<void> {
    await this.page.getByText(label).click();
  }

  // Switches tool via the nav anchor (e.g. 'Gene Browser',
  // 'Genotype Browser').
  public async openToolLink(label: string): Promise<void> {
    await this.page.locator('a').filter({ hasText: label }).click();
  }
}
