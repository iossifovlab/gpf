import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-gene-profiles-table` and its
// column-filtering menus, compare-genes modal, tabs and sorting.
export class GeneProfilesTable {
  public readonly root: Locator;
  public readonly loading: Locator;

  // Rows and cells.
  public readonly rows: Locator;
  public readonly dataRows: Locator;
  public readonly nothingFound: Locator;
  public readonly rowCells: Locator;

  // Header.
  public readonly headerCells: Locator;
  public readonly headerContentSpans: Locator;
  public readonly tableHeader: Locator;
  public readonly activeSortHeader: Locator;
  public readonly sortingButtons: Locator;

  // Search.
  public readonly searchInput: Locator;
  public readonly searchLoadingIcon: Locator;
  public readonly searchClearIcon: Locator;
  public readonly progressActivity: Locator;

  // Category / column filtering menu.
  public readonly categoryFilteringButton: Locator;
  public readonly multipleSelectMenu: Locator;
  public readonly menuCheckUncheckAllButton: Locator;
  public readonly menuSearchInput: Locator;
  public readonly menuLabels: Locator;
  public readonly checkUncheckAllButton: Locator;

  // Compare genes.
  public readonly compareGenesModal: Locator;
  public readonly compareGeneItems: Locator;
  public readonly compareGenesClose: Locator;
  public readonly compareGenesCompareButton: Locator;

  // Tabs.
  public readonly allGenesButton: Locator;
  public readonly tabs: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-profiles-table');
    this.loading = page.locator('#loading');

    this.rows = page.locator('.table-body-row');
    this.dataRows = page.locator('.table-body-row:not(#nothing-found)');
    this.nothingFound = page.locator('#nothing-found');
    this.rowCells = page.locator('.row-cell');

    this.headerCells = page.locator('.header-cell');
    this.headerContentSpans = page.locator('.header-cell-content-span');
    this.tableHeader = page.locator('#table-header');
    this.activeSortHeader = page.locator('div.active-sort-header');
    this.sortingButtons = page.locator('gpf-sorting-buttons');

    this.searchInput = page.locator('input#gene-search-input');
    this.searchLoadingIcon = page.locator('.search-loading-icon');
    this.searchClearIcon = page.locator('.search-clear-icon');
    this.progressActivity = page.getByText('progress_activity');

    this.categoryFilteringButton = page.locator('#category-filtering-button');
    this.multipleSelectMenu = page.locator('gpf-multiple-select-menu');
    this.menuCheckUncheckAllButton = this.multipleSelectMenu.locator('#check-uncheck-all-button');
    this.menuSearchInput = this.multipleSelectMenu.locator('input[name="search"]');
    this.menuLabels = this.multipleSelectMenu.locator('label');
    this.checkUncheckAllButton = page.locator('#check-uncheck-all-button');

    this.compareGenesModal = page.locator('#compare-genes-modal');
    this.compareGeneItems = page.locator('.compare-gene-item');
    this.compareGenesClose = page.locator('.compare-genes-close');
    this.compareGenesCompareButton = page.locator('#compare-genes-compare-button');

    this.allGenesButton = page.getByRole('button', { name: 'All genes' });
    this.tabs = page.locator('div.tab');
  }

  // The column-filtering button for a category id
  // (e.g. 'autism_gene_sets_rank', 'protection_scores').
  public columnFilteringButton(id: string): Locator {
    return this.page.locator(`#${id}-column-filtering-button`);
  }

  // The clickable gene cell/link in the table for a gene symbol, matched
  // by its exact text (e.g. 'CHD8'); clicking it opens the single view.
  public geneCell(gene: string): Locator {
    return this.page.locator('div').filter({ hasText: new RegExp(`^${gene}$`) });
  }

  // A data row by index.
  public row(index: number): Locator {
    return this.dataRows.nth(index);
  }

  // A data row filtered by contained text (e.g. 'RAPGEF4').
  public rowByText(text: string): Locator {
    return this.rows.filter({ hasText: text });
  }

  // A header cell filtered by contained text.
  public headerCellByText(text: string): Locator {
    return this.headerCells.filter({ hasText: text });
  }

  // A menu option (label) by its accessible label.
  public menuOption(label: string): Locator {
    return this.multipleSelectMenu.getByLabel(label);
  }
}
