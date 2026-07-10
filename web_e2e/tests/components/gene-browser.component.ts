import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gene-browser` view (search box, gene
// plot, filter panels and download controls).
export class GeneBrowser {
  public readonly root: Locator;
  public readonly geneSymbolLabel: Locator;
  public readonly searchBox: Locator;
  public readonly goButton: Locator;
  public readonly goInput: Locator;
  public readonly goRoleButton: Locator;
  public readonly codingOnlyCheckbox: Locator;
  public readonly genePlot: Locator;
  public readonly previewTable: Locator;
  public readonly filters: Locator;

  // Filter panels.
  public readonly affectedStatusFilters: Locator;
  public readonly effectTypesFilters: Locator;
  public readonly inheritanceTypesFilters: Locator;
  public readonly variantTypesFilters: Locator;

  // Family-variants table + count.
  public readonly familyVariantsCount: Locator;
  public readonly familyVariantsCountSpan: Locator;
  public readonly familyVariantsCountBadge: Locator;
  public readonly downloadFamilyVariantsButton: Locator;
  public readonly nothingFoundRow: Locator;
  public readonly tableRows: Locator;

  // Gene-plot header controls.
  public readonly undoButton: Locator;
  public readonly redoButton: Locator;
  public readonly resetButton: Locator;
  public readonly variantsCountSpan: Locator;
  public readonly hideTranscripts: Locator;
  public readonly condenseIntrons: Locator;
  public readonly geneTitle: Locator;
  public readonly summaryAllelesCount: Locator;
  public readonly summaryAllelesCountSpan: Locator;
  public readonly downloadSummaryVariantsButton: Locator;
  public readonly downloadSummaryVariantsTitle: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-browser');
    this.geneSymbolLabel = page.getByText('Gene Symbol');
    this.searchBox = this.root.locator('input#search-box');
    this.goButton = page.getByText('Go');
    this.goInput = page.locator('input[value=\'Go\']');
    this.goRoleButton = page.getByRole('button', { name: 'Go' });
    this.codingOnlyCheckbox = page.locator('input#coding-only-checkbox');
    this.genePlot = page.locator('gpf-gene-plot');
    this.previewTable = page.locator('gpf-genotype-preview-table');
    this.filters = page.locator('#filters');

    this.affectedStatusFilters = page.locator('#affected-status-filters');
    this.effectTypesFilters = page.locator('#effect-types-filters');
    this.inheritanceTypesFilters = page.locator('#inheritance-types-filters');
    this.variantTypesFilters = page.locator('#variant-types-filters');

    this.familyVariantsCount = page.locator('#family-variants-count');
    this.familyVariantsCountSpan = page.locator('#family-variants-count span');
    this.familyVariantsCountBadge = page.locator('span#family-variants-count');
    this.downloadFamilyVariantsButton = page.locator('#download-family-variants-button');
    this.nothingFoundRow = page.locator('#nothing-found-row');
    this.tableRows = page.locator('.table-row');

    this.undoButton = page.locator('#undo-button');
    this.redoButton = page.locator('#redo-button');
    this.resetButton = page.locator('#reset-button');
    this.variantsCountSpan = page.locator('#variants-count-span');
    this.hideTranscripts = page.getByText('Hide transcripts');
    this.condenseIntrons = page.getByText('Condense introns');
    this.geneTitle = page.locator('#gene-title');
    this.summaryAllelesCount = page.locator('#summary-alleles-count');
    this.summaryAllelesCountSpan = page.locator('#summary-alleles-count span');
    this.downloadSummaryVariantsButton = page.locator('#download-summary-variants-button');
    this.downloadSummaryVariantsTitle = page.getByTitle('Download summary variants');
  }

  // Searches for a gene and waits for its plot to render.
  public async searchGene(symbol: string): Promise<void> {
    await this.searchBox.fill(symbol);
    await this.goButton.click();
  }

  // --- Filter accessors: first-match variants (gene-browser view) ---
  public affectedStatusFilter(name: string): Locator {
    return this.affectedStatusFilters.getByLabel(name).nth(0);
  }

  public effectTypesFilter(name: string): Locator {
    return this.effectTypesFilters.locator('span').getByText(name).nth(0);
  }

  public inheritanceTypesFilter(name: string): Locator {
    return this.inheritanceTypesFilters.locator('span').getByText(name).nth(0);
  }

  public variantTypesFilter(name: string): Locator {
    return this.variantTypesFilters.locator('span').getByText(name).nth(0);
  }

  public filter(field: string, name: string): Locator {
    switch (field) {
      case 'affectedStatus':
        return this.affectedStatusFilter(name);
      case 'effectTypes':
        return this.effectTypesFilter(name);
      case 'inheritanceTypes':
        return this.inheritanceTypesFilter(name);
      case 'variantTypes':
        return this.variantTypesFilter(name);
      default:
        throw new Error(`Unknown filter field: ${field}`);
    }
  }

  // Returns the filter panel locator for a field key.
  public panel(field: string): Locator {
    switch (field) {
      case 'affectedStatus':
        return this.affectedStatusFilters;
      case 'effectTypes':
        return this.effectTypesFilters;
      case 'inheritanceTypes':
        return this.inheritanceTypesFilters;
      case 'variantTypes':
        return this.variantTypesFilters;
      default:
        throw new Error(`Unknown filter field: ${field}`);
    }
  }

  // --- Filter accessors: exact-match variants (gene-plot view) ---
  public affectedStatusFilterExact(name: string): Locator {
    return this.affectedStatusFilters.getByLabel(name, { exact: true });
  }

  public effectTypesFilterExact(name: string): Locator {
    return this.effectTypesFilters.getByText(name, { exact: true });
  }

  public inheritanceTypesFilterExact(name: string): Locator {
    return this.inheritanceTypesFilters.getByText(name, { exact: true });
  }

  public variantTypesFilterExact(name: string): Locator {
    return this.variantTypesFilters.getByLabel(name, { exact: true });
  }
}
