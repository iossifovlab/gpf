import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';
import { PhenoBrowserPage } from 'cypress/elements/pheno-browser-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Datasets tests', () => {
  const page = new DatasetsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
  });

  beforeEach(() => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics, false);
  });

  afterEach(() => {
    page.logout();
  });

  it('should toggle studies dropdown menu', () => {
    page.loginAdmin();
    page.datasetsDropdownMenuButton.invoke('attr', 'aria-expanded').should('contain', 'false');
    page.datasetsDropdownMenuButton.click();
    page.datasetsDropdownMenuButton.invoke('attr', 'aria-expanded').should('contain', 'true');
    page.datasetsDropdownMenuButton.click();
    page.datasetsDropdownMenuButton.invoke('attr', 'aria-expanded').should('contain', 'false');
  });

  it('should display genotype browser', () => {
    const genotypeBrowserPage = new GenotypeBrowserPage();

    page.loginAdmin();
    genotypeBrowserPage.window.should('not.exist');

    page.genotypeBrowserButton.click();
    genotypeBrowserPage.window.should('be.visible');
  });

  it('should display dataset statistics window', () => {
    page.loginAdmin();
    page.datasetStatisticsWindow.should('be.visible');

    page.genotypeBrowserButton.click();
    page.datasetStatisticsWindow.should('not.exist');

    page.datasetStatisticsButton.click();
    page.datasetStatisticsWindow.should('be.visible');
  });

  it('should display phenotype browser window', () => {
    const phenoBrowserPage = new PhenoBrowserPage();

    page.loginAdmin();
    phenoBrowserPage.window.should('not.exist');

    page.phenotypeBrowserButton.click();
    phenoBrowserPage.window.should('be.visible');

    page.datasetStatisticsButton.click();
    phenoBrowserPage.window.should('not.exist');
  });

  it('should display phenotype tool window', () => {
    const phenoToolPage = new PhenoToolPage();

    page.loginAdmin();
    page.phenotypeToolButton.click();
    phenoToolPage.window.should('be.visible');

    page.datasetStatisticsButton.click();
    phenoToolPage.window.should('not.exist');
  });

  it('should change url correctly after clicking on a dataset from the dataset dropdown menu', () => {
    const datasets = [
      {id: datasetIds.allGenotypes, url: 'ALL_genotypes'},
      {id: datasetIds.compGenotypes, url: 'COMP_genotypes'},
      {id: datasetIds.compDenovo, url: 'comp_denovo'},
      {id: datasetIds.compVcf, url: 'comp_vcf'},
      {id: datasetIds.compAll, url: 'comp_all'},
      {id: datasetIds.iossifov2014, url: 'iossifov_2014'},
      {id: datasetIds.multi, url: 'multi'}
    ]

    page.loginAdmin();

    datasets.forEach(dataset => {
      page.datasetsDropdownMenuButton.click();
      page.datasetsDropdownMenuElements.should('be.visible');
      page.datasetsDropdownMenuElements.contains(dataset.id).click();
      cy.url().then(url => {
        expect(url).to.contain(Cypress.config().baseUrl + 'datasets/' + dataset.url + '/');
      });
    });
  });
});
