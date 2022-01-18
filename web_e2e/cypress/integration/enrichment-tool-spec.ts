import 'reflect-metadata';
import { plainToClass } from 'class-transformer';
import * as YAML from 'yaml';
import { EnrichmentToolPage } from 'cypress/elements/enrichment-tool-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { EnrichmentToolData } from 'cypress/elements/dynamic-data-structure';

describe('Enrichment tool common tests', () => {
  const page = new EnrichmentToolPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.enrichmentTool);
  });

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.window.should('be.visible');
  });

  it('should display enrichment models block', () => {
    page.enrichmentModelsBlock.should('be.visible');
  });

  it('should display "Enrichment Test" button', () => {
    page.enrichmentTestButton.should('be.visible');
  });

  it('should display "Share query" button', () => {
    const shareQueryPage = new ShareQueryPage();
    shareQueryPage.button.should('be.visible');
  });

  it('should display "Save query" button', () => {
    const saveQueryPage = new SaveQueryPage();
    saveQueryPage.button.should('be.visible');
  });

  it('should display enrichment table after "Enrichment Test" button click', () => {
    const genesBlockPage = new GenesBlockPage();

    page.table.should('not.exist');

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    page.enrichmentTestButton.click();
    page.table.should('be.visible');
  });

  it('should display alert window after "Enrichment Test" button click when the gene symbols textarea is empty', () => {
    const genesBlockPage = new GenesBlockPage();

    page.findWarningAlertInComponent('gpf-gene-symbols').should('be.visible');

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    page.findWarningAlertInComponent('gpf-gene-symbols').should('be.hidden');
  });

  it('should display alert window when the gene sets textarea is empty', () => {
    const genesBlockPage = new GenesBlockPage();

    page.findErrorAlertInComponent('gpf-gene-sets').should('not.exist');

    genesBlockPage.geneSetsButton.click();
    page.findErrorAlertInComponent('gpf-gene-sets').should('be.visible');

    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('synaptic clefts inhibitory');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('synaptic clefts inhibitory').click();
    page.enrichmentTestButton.click();
    page.findErrorAlertInComponent('gpf-gene-sets').should('not.exist');
  });

  it('should display "55" and "169" in the affected person"s observed column of LGDs and missense"s rows respectively ' +
     'with gene set Main: FMRP Darnell', () => {
    const genesBlockPage = new GenesBlockPage();
    
    genesBlockPage.geneSetsButton.click();
    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('FMRP Darnell');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('FMRP Darnell').click();
    page.enrichmentTestButton.click();
    page.findTableField('affected', 'LGDs', 2).should('have.text', '55');
    page.findTableField('affected', 'Missense', 2).should('have.text', '169');

    page.findTableField('affected', 'LGDs', 3).should('have.text', '35.02');
    page.findTableField('affected', 'Missense', 3).should('have.text', '145.68');
  });

  it('should display "0" and "2" in the affected person"s observed column of LGDs and missense"s rows respectively ' +
     'with gene set MSigDB Pathways: BIOCARTA_PTEN_PATHWAY', () => {
    const genesBlockPage = new GenesBlockPage();

    genesBlockPage.geneSetsButton.click();
    genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select('MSigDB Pathways', {force: true});
    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('BIOCARTA_PTEN_PATHWAY');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('BIOCARTA_PTEN_PATHWAY').click();
    page.enrichmentTestButton.click();
    page.findTableField('affected', 'LGDs', 2).should('have.text', '0');
    page.findTableField('affected', 'Missense', 2).should('have.text', '2');

    page.findTableField('affected', 'LGDs', 3).should('have.text', '0.36');
    page.findTableField('affected', 'Missense', 3).should('have.text', '1.52');
  });

});


// Pass path to yaml file using the '--env' flag in the cypress command:
// npx cypress open --config baseUrl=http://172.20.0.5/gpf/ --env yamlPath=cypress/iossifov.data.expected.yaml
function parseYamlData(filePath: string): EnrichmentToolData[] {
  return plainToClass(EnrichmentToolData, YAML.parse(filePath) as EnrichmentToolData[]);
}

const dynamicData: EnrichmentToolData[] = parseYamlData(Cypress.env('yamlFile'));

describe.only('Enrichment tool data tests', () => {
  const page = new EnrichmentToolPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.enrichmentTool);
  });

  it('print yaml', () => {
    console.log(dynamicData);
  });

  dynamicData.forEach(data => {
    it(data.name, () => {
      console.log(data.name);
    });
  })
});
