// import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
// import { GenePlotPage } from 'cypress/elements/gene-plot-page';
// import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

// describe('Gene browser visual tests', () => {
//   const geneBrowserPage = new GeneBrowserPage();
//   const genePlotPage = new GenePlotPage();

//   before(() => {
//     geneBrowserPage.cleanup();
//     geneBrowserPage.navigateToHome(false);
//     geneBrowserPage.loginAdmin();
//     geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
//     geneBrowserPage.prepareForVisualTest();
//   });

//   it('should condense introns', () => {
//     geneBrowserPage.searchInputBox.type('chd8');
//     geneBrowserPage.pressGoButton();
//     genePlotPage.condenseIntronsCheckbox.click();
//     genePlotPage.window.matchImage();

//     genePlotPage.condenseIntronsCheckbox.click();
//     genePlotPage.window.matchImage();
//   });

//   it('should compare visually TTN gene plot results', () => {
//     geneBrowserPage.searchInputBox.type('ttn');
//     geneBrowserPage.pressGoButton();
//     genePlotPage.window.matchImage();
//   });
// });