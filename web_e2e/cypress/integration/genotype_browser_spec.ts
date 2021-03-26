import { GenotypeBrowserPage } from "cypress/elements/genotype_browser_page";
import { RegionsBlockPage } from "cypress/elements/regions_block_page";
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
  
    // using(datasetList, (dataset) => {
    //   it('should display genotype preview table after table preview button click at /' + dataset + '/browser',  () => {
    //     const genotypePreviewTablePage = new GenotypePreviewTablePage();
    //     const genotypePreviewTable = genotypePreviewTablePage.table;
  
    //     await genotypeBrowserPage.navigateToDatasetPage(dataset, toolPageNames.genotypeBrowser);
    //     await genotypeBrowserPage.browserWaitForVisibilityOfElement(genotypeBrowserPage.window);
    //     await expect(await genotypePreviewTable.isPresent()).toBe(false);
  
    //     await genotypeBrowserPage.browserWaitForVisibilityOfElement(genotypeBrowserPage.tablePreviewButton);
    //     await genotypeBrowserPage.browserWaitForElementToBeClickable(genotypeBrowserPage.tablePreviewButton);
    //     await browser.sleep(500);
    //     await genotypeBrowserPage.tablePreviewButton.click();
    //     await genotypeBrowserPage.browserWaitForVisibilityOfElement(genotypePreviewTable);
    //     await expect(await genotypePreviewTable.isDisplayed()).toBe(true);
  
    //     // Wait for the loading screen to close so the logout button can be clickable.
    //     // This isn't necessary for the other tests, as they wait for the overview pagraph,
    //     // which loads after the loading screen is closed.
    //     await genotypeBrowserPage.browserWaitForInvisibilityOfElement(genotypeBrowserPage.loadingScreenElement);
    //   });
    // });
  });