import { Locator, Page } from '@playwright/test';

// Component object for the datasets dropdown / navigation surface and the
// per-tool content roots reachable from a dataset page.
export class Datasets {
  public readonly dropdownButton: Locator;
  public readonly datasetNodes: Locator;
  public readonly alertDanger: Locator;
  public readonly registerAlert: Locator;
  public readonly datasetDescriptionButton: Locator;

  // Per-tool content roots.
  public readonly genotypeBrowser: Locator;
  public readonly phenoBrowser: Locator;
  public readonly phenoTool: Locator;
  public readonly variantReports: Locator;
  public readonly geneBrowser: Locator;

  public constructor(private readonly page: Page) {
    this.dropdownButton = page.locator('#datasets-dropdown-menu-button');
    this.datasetNodes = page.locator('gpf-dataset-node a');
    this.alertDanger = page.locator('.alert-danger');
    this.registerAlert = page.locator('#register-alert');
    this.datasetDescriptionButton = page.getByText('Dataset Description');

    this.genotypeBrowser = page.locator('gpf-genotype-browser');
    this.phenoBrowser = page.locator('gpf-pheno-browser');
    this.phenoTool = page.locator('gpf-pheno-tool');
    this.variantReports = page.locator('gpf-variant-reports');
    this.geneBrowser = page.locator('gpf-gene-browser');
  }

  // A tool tab/link on a dataset page by its visible text
  // (e.g. 'Genotype browser', 'Dataset Statistics').
  public toolLink(name: string): Locator {
    return this.page.getByText(name);
  }

  // A dataset node anchor in the tree filtered by dataset id/name.
  public datasetNode(id: string): Locator {
    return this.datasetNodes.filter({ hasText: id });
  }

  // A dataset dropdown anchor filtered by dataset id/name.
  public dropdownLink(id: string): Locator {
    return this.page.locator('a').filter({ hasText: id });
  }

  // An access-rights icon inside the selected-dataset dropdown button
  // (e.g. '.transmitted-icon', '.phenotype-icon').
  public dropdownButtonIcon(iconClass: string): Locator {
    return this.dropdownButton.locator(iconClass);
  }
}
