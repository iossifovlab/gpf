import { EnrichmentToolPage } from 'cypress/elements/enrichment-tool-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { applyData, EnrichmentToolData, parseYamlData } from 'cypress/elements/dynamic-data-structure';

describe('Enrichment tool common tests', () => {
  const page = new EnrichmentToolPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
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

  it('should display "55" and "169" in the affected person\'s observed column ' +
     'of LGDs and missense\'s rows respectively with gene set Main: FMRP Darnell', () => {
    const genesBlockPage = new GenesBlockPage();

    genesBlockPage.geneSetsButton.click();
    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('FMRP Darnell');
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('FMRP Darnell').click();
    page.enrichmentTestButton.click();
    page.findTableCell('affected', 'LGDs', 2).should('have.text', '55');
    page.findTableCell('affected', 'Missense', 2).should('have.text', '169');

    page.findTableCell('affected', 'LGDs', 3).should('have.text', '35.02');
    page.findTableCell('affected', 'Missense', 3).should('have.text', '145.68');
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
    page.findTableCell('affected', 'LGDs', 2).should('have.text', '0');
    page.findTableCell('affected', 'Missense', 2).should('have.text', '2');

    page.findTableCell('affected', 'LGDs', 3).should('have.text', '0.36');
    page.findTableCell('affected', 'Missense', 3).should('have.text', '1.52');
  });
});


if (Cypress.env().yamlPath !== undefined) {
  const dynamicData: EnrichmentToolData[] = parseYamlData(Cypress.env('yamlFile'));

  describe('Enrichment tool data tests', () => {
    const page = new EnrichmentToolPage();

    before(() => {
      page.cleanup();
      page.navigateToHome(false);
      page.loginAdmin();
    });

    beforeEach(() => {
      page.preserveLogin();
      page.navigateToHome();
      page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.enrichmentTool);
    });

    dynamicData.forEach(dataEntry => {
      describe(dataEntry.name, () => {
        dataEntry.cases.forEach(case_ => {
          it(case_.name, () => {
            applyData(case_.params);

            page.enrichmentTestButton.click();

            case_.expected.forEach(async expected_ => {
              const rowId = expected_.rowId.split('_');
              const affectedStatus: string = rowId[0];
              const effectType: string = rowId[1];

              const actualValues: string[] = await page.getRowValues(affectedStatus, effectType);

              expect(actualValues).to.deep.eq(expected_.values);
            });
          });
        });
      });
    })
  });
}

