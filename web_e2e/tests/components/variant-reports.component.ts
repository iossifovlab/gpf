import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-variant-reports` (Dataset Statistics)
// view: the families-by-number / by-pedigree / de-novo tabs, tag filter
// modal, legend and pedigree chart modal.
export class VariantReports {
  public readonly root: Locator;

  // Families by number.
  public readonly downloadTotalFamilies: Locator;
  public readonly familiesByNumberSelect: Locator;
  public readonly familiesByNumberDiv: Locator;
  public readonly downloadLink: Locator;

  // Families by pedigree.
  public readonly familiesByPedigree: Locator;
  public readonly familiesByPedigreeSelect: Locator;
  public readonly familiesByPedigreeDiv: Locator;
  public readonly downloadButton: Locator;
  public readonly selectTags: Locator;
  public readonly expandLegendButton: Locator;
  public readonly legend: Locator;
  public readonly legendItems: Locator;
  public readonly pedigreeCells: Locator;
  public readonly nothingFound: Locator;

  // Tags modal.
  public readonly tagsModalContent: Locator;
  public readonly tagList: Locator;
  public readonly selectedTagsList: Locator;
  public readonly andButton: Locator;
  public readonly orButton: Locator;
  public readonly clearFilters: Locator;

  // De Novo variants.
  public readonly denovoVariantsSelect: Locator;
  public readonly denovoVariantsLegendReport: Locator;
  public readonly denovoVariantsDiv: Locator;

  // Pedigree chart modal.
  public readonly modalContent: Locator;
  public readonly modalPedigreeContainer: Locator;
  public readonly modalFamilyCount: Locator;
  public readonly modalDownloadButton: Locator;
  public readonly familyIdsList: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-variant-reports');

    this.downloadTotalFamilies = page.locator('#download-total-families');
    this.familiesByNumberSelect = page.locator('#families-by-number-select');
    this.familiesByNumberDiv = page.locator('#families-by-number-div');
    this.downloadLink = page.locator('.download-link');

    this.familiesByPedigree = page.locator('#families-by-pedigree');
    this.familiesByPedigreeSelect = page.locator('#families-by-pedigree-select');
    this.familiesByPedigreeDiv = page.locator('#families-by-pedigree-div');
    this.downloadButton = page.locator('#download-button');
    this.selectTags = page.getByText('Select tags');
    this.expandLegendButton = page.locator('#expand-legend-button');
    this.legend = page.locator('#legend');
    this.legendItems = page.locator('.legend-item');
    this.pedigreeCells = page.locator('.pedigree-cell');
    this.nothingFound = page.locator('#nothing-found');

    this.tagsModalContent = page.locator('#tags-modal-content');
    this.tagList = page.locator('#tag-list');
    this.selectedTagsList = page.locator('#selected-tags-list');
    this.andButton = page.getByRole('button', { name: 'And' });
    this.orButton = page.getByRole('button', { name: 'Or' });
    this.clearFilters = page.getByText('Clear filters');

    this.denovoVariantsSelect = page.locator('#denovo-variants-select');
    this.denovoVariantsLegendReport = page.locator('#de-novo-variants-legend-report');
    this.denovoVariantsDiv = page.locator('#denovo-variants-div');

    this.modalContent = page.locator('.modal-content');
    this.modalPedigreeContainer = page.locator('#modal-pedigree-container');
    this.modalFamilyCount = page.locator('#modal-family-count');
    this.modalDownloadButton = page.locator('.modal-content >> #download-button');
    this.familyIdsList = page.locator('#family-ids-list > div');
  }

  // A report tab by its visible text (e.g. 'Families by number',
  // 'Families by pedigree', 'De Novo variants').
  public tab(name: string): Locator {
    return this.page.getByText(name);
  }

  // The add ("+") control for a family tag id.
  public tagAdd(tag: string): Locator {
    return this.page.locator(`#${tag}-tag-add`);
  }

  // The remove ("-") control for a family tag id.
  public tagRemove(tag: string): Locator {
    return this.page.locator(`#${tag}-tag-remove`);
  }
}
