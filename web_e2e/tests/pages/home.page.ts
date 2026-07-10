import { Locator, Page } from '@playwright/test';
import { Header } from '../components/header.component';
import { Datasets } from '../components/datasets.component';

// Page object for the `gpf-home` landing page (gene search, gene-profiles
// entry and the dataset tree with access-rights icons).
export class HomePage {
  public readonly header: Header;
  public readonly datasets: Datasets;

  public readonly root: Locator;
  public readonly geneProfilesSection: Locator;
  public readonly searchBox: Locator;
  public readonly allGenes: Locator;
  public readonly geneProfilesBlock: Locator;
  public readonly geneProfilesSingleView: Locator;
  public readonly noGeneFound: Locator;
  public readonly registerAlert: Locator;
  public readonly selectedDatasetName: Locator;
  public readonly collapseIcons: Locator;
  public readonly geneBrowser: Locator;

  public constructor(private readonly page: Page) {
    this.header = new Header(page);
    this.datasets = new Datasets(page);

    this.root = page.locator('gpf-home');
    this.geneProfilesSection = page.locator('#gene-profiles-section');
    this.searchBox = page.locator('#search-box');
    this.allGenes = page.getByText('All genes');
    this.geneProfilesBlock = page.locator('gpf-gene-profiles-block');
    this.geneProfilesSingleView = page.locator('gpf-gene-profiles-single-view');
    this.noGeneFound = page.getByText('No such gene found!');
    this.registerAlert = page.locator('#register-alert');
    this.selectedDatasetName = page.locator('#selected-dataset-name');
    this.collapseIcons = page.locator('.collapse-dataset-icon');
    this.geneBrowser = page.locator('gpf-gene-browser');
  }

  // A dataset / navigation anchor by its exact visible text.
  public datasetLink(name: string): Locator {
    return this.page.locator(`a:text("${name}")`);
  }

  // The per-dataset icon wrapper on the home page (e.g. dataset id
  // 'denovo_helloworld' -> '#denovo_helloworld-icons-wrapper').
  public iconsWrapper(datasetId: string): Locator {
    return this.page.locator(`#${datasetId}-icons-wrapper`);
  }

  // A gene search autocomplete option by name.
  public option(name: string): Locator {
    return this.page.getByRole('option', { name });
  }
}
