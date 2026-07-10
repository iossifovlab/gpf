import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-pheno-browser-table` (search, instrument
// dropdown, measure rows, descriptions and downloads).
export class PhenoBrowser {
  public readonly root: Locator;
  public readonly searchInput: Locator;
  public readonly instrumentDropdown: Locator;
  public readonly instrumentCells: Locator;
  public readonly measureNameCells: Locator;
  public readonly measureTypeCells: Locator;
  public readonly ageCells: Locator;
  public readonly iqCells: Locator;
  public readonly nothingFound: Locator;
  public readonly tooltipInner: Locator;
  public readonly downloadMeasures: Locator;
  public readonly tableChart: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-pheno-browser-table');
    this.searchInput = page.locator('input.form-control');
    this.instrumentDropdown = page.locator('select.form-control');
    this.instrumentCells = page.locator('.instrument-cell');
    this.measureNameCells = page.locator('.measure-name-cell');
    this.measureTypeCells = page.locator('.measure-type-cell ');
    this.ageCells = page.locator('.age');
    this.iqCells = page.locator('.iq');
    this.nothingFound = page.getByText('Nothing found');
    this.tooltipInner = page.locator('.tooltip-inner');
    this.downloadMeasures = page.locator('#download-measures');
    this.tableChart = page.locator('img.table-chart');
  }

  // The "Measures count: N" label.
  public measuresCount(count: number): Locator {
    return this.page.getByText(`Measures count: ${count}`);
  }

  // The description tooltip toggle icon for a measure id.
  public descriptionIcon(measure: string): Locator {
    return this.page.locator(`[id="${measure}-description-icon"]`);
  }

  // An exact-text column header (e.g. 'Instrument', 'Pheno Measure', 'male').
  public columnHeader(name: string): Locator {
    return this.page.getByText(name, { exact: true });
  }

  // A per-measure regression p-value cell by measure and sex
  // (e.g. measure 'age', sex 'Male' -> class "age.pvalueRegressionMale").
  public regressionCell(measure: string, sex: 'Male' | 'Female'): Locator {
    return this.page.locator(`[class="${measure}.pvalueRegression${sex}"]`);
  }
}
