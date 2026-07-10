import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gene-profiles-single-view` (score and
// gene-set tables, datasets table, external links and tabs).
export class GeneProfilesSingleView {
  public readonly root: Locator;
  public readonly heading: Locator;

  // Score / gene-set tables.
  public readonly autismScores: Locator;
  public readonly protectionScores: Locator;
  public readonly autismGeneSets: Locator;
  public readonly relevantGeneSets: Locator;
  public readonly singleScoreMarkers: Locator;
  public readonly geneSetsTable: Locator;
  public readonly datasetsTable: Locator;

  // Tabs.
  public readonly tabsWrapper: Locator;
  public readonly tableHeader: Locator;
  public readonly closeTabButtons: Locator;

  // Error modal.
  public readonly errorModal: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-profiles-single-view');
    this.heading = this.root.locator('h2');

    this.autismScores = page.locator('#autism_scores');
    this.protectionScores = page.locator('#protection_scores');
    this.autismGeneSets = page.locator('#autism_gene_sets');
    this.relevantGeneSets = page.locator('#relevant_gene_sets');
    this.singleScoreMarkers = page.locator('.single-score-marker');
    this.geneSetsTable = page.locator('.gene-sets-table');
    this.datasetsTable = page.locator('.datasets-table');

    this.tabsWrapper = page.locator('#tabs-wrapper');
    this.tableHeader = page.locator('#table-header');
    this.closeTabButtons = this.tabsWrapper.locator('.close-tab-button');

    this.errorModal = page.locator('.error-modal');
  }

  // An external / navigation link by its accessible name.
  public link(name: string): Locator {
    return this.page.getByRole('link', { name });
  }

  // The heading of the single view for a given gene symbol.
  public headingFor(gene: string): Locator {
    return this.root.locator(`h2:text("${gene}")`);
  }

  // A tab button by its gene-symbol name.
  public tab(name: string): Locator {
    return this.page.getByRole('button', { name });
  }
}
