import { EnrichmentToolPage } from 'cypress/elements/enrichment-tool-page';
import { ErrorsAlertPage } from 'cypress/elements/errors-alert-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Enrichment tool tests', () => {
  const enrichmentToolPage = new EnrichmentToolPage();

  before(() => {
    enrichmentToolPage.cleanup();
    enrichmentToolPage.navigateToHome();
    enrichmentToolPage.loginAdmin();
  });

  beforeEach(() => {
    enrichmentToolPage.preserveLogin();
    enrichmentToolPage.navigateToHome();
  });

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    genesBlockPage.window.should('be.visible');
  });

  it('should display enrichment models block', () => {
    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    enrichmentToolPage.enrichmentModelsBlock.should('be.visible');
  });

  it('should display \'Enrichment Test\' button', () => {
    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    enrichmentToolPage.enrichmentTestButton.should('be.visible');
  });

  it('should display \'Share query\' button', () => {
    const shareQueryPage = new ShareQueryPage();
    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    shareQueryPage.button.should('be.visible');
  });

  it('should display \'Save query\' button', () => {
    const saveQueryPage = new SaveQueryPage();
    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    saveQueryPage.button.should('be.visible');
  });

  it('should display enrichment table after \'Enrichment Test\' button click', () => {
    const genesBlockPage = new GenesBlockPage();

    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    enrichmentToolPage.table.should('not.exist');

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    enrichmentToolPage.enrichmentTestButton.click();
    enrichmentToolPage.table.should('be.visible');
  });

  it('should display alert window after \'Enrichment Test\' button click when the gene symbols textarea is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();
    const genesBlockPage = new GenesBlockPage();

    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-symbols').should('be.visible');

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    enrichmentToolPage.enrichmentTestButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-symbols').should('not.exist');
  });

  // review
  // investigate consitency issues when running all enrichment tool tests
  // works fine when ran by itself though
  it('should display alert window when the gene sets textarea is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();
    const genesBlockPage = new GenesBlockPage();

    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-sets').should('not.exist');

    genesBlockPage.geneSetsButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-sets').should('be.visible');

    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('synaptic clefts inhibitory');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('synaptic clefts inhibitory').click();
    enrichmentToolPage.enrichmentTestButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-sets').should('not.exist');
  });

  it('should display \'55\' and \'169\' in the affected person\'s observed column of LGDs and missense\'s rows respectively ' +
     'with gene set Main: FMRP Darnell', () => {
    const genesBlockPage = new GenesBlockPage();

    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    genesBlockPage.geneSetsButton.click();
    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('FMRP Darnell');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('FMRP Darnell').click();
    enrichmentToolPage.enrichmentTestButton.click();
    enrichmentToolPage.findTableField('affected', 'LGDs', 1).should('have.text', '55');
    enrichmentToolPage.findTableField('affected', 'Missense', 1).should('have.text', '169')
  });

  it('should display \'0\' and \'2\' in the affected person\'s observed column of LGDs and missense\'s rows respectively ' +
     'with gene set MSigDB Pathways: BIOCARTA_PTEN_PATHWAY', () => {
    const genesBlockPage = new GenesBlockPage();

    enrichmentToolPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.enrichmentTool);
    genesBlockPage.geneSetsButton.click();
    genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select('MSigDB Pathways');
    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('BIOCARTA_PTEN_PATHWAY');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('BIOCARTA_PTEN_PATHWAY').click();
    enrichmentToolPage.enrichmentTestButton.click();
    enrichmentToolPage.findTableField('affected', 'LGDs', 1).should('have.text', '0');
    enrichmentToolPage.findTableField('affected', 'Missense', 1).should('have.text', '2');
  });
});
