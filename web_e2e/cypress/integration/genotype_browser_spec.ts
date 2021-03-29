import { GenotypeBrowserPage } from "cypress/elements/genotype-browser-page";
import { GenotypePreviewTablePage } from "cypress/elements/genotype-preview-table-page";
import { RegionsBlockPage } from "cypress/elements/regions-block-page";
import { datasetIds, toolPageNames } from "cypress/elements/utils";

describe('Genotype browser tests', () => {
  const genotypeBrowserPage = new GenotypeBrowserPage();
  const datasetList = [
    datasetIds.compAll, datasetIds.compDenovo, datasetIds.compVcf, datasetIds.iossifov2014, datasetIds.multi
  ];

  beforeEach(() => {
    genotypeBrowserPage.navigateToHome();
    genotypeBrowserPage.loginAdmin();
  });

  afterEach(() => {
    genotypeBrowserPage.logout();
  });

  datasetList.forEach(dataset => {
    it('should display regions block panel in genotype browser at /' + dataset + '/browser', () => {
      const regionsBlockPage = new RegionsBlockPage();
      genotypeBrowserPage.navigateToDatasetPage(dataset, toolPageNames.genotypeBrowser);
      regionsBlockPage.block.should('be.visible');
    });
  });
  
  datasetList.forEach(dataset => {
    it.only('should display genotype preview table after table preview button click at /' + dataset + '/browser',  () => {
      const genotypePreviewTablePage = new GenotypePreviewTablePage();

      genotypeBrowserPage.navigateToDatasetPage(dataset, toolPageNames.genotypeBrowser);
      genotypePreviewTablePage.table.should('not.exist');

      genotypeBrowserPage.tablePreviewButton.click();
      genotypePreviewTablePage.table.should('be.visible');
    });
  });
});