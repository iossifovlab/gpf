import { EnrichmentToolPage } from 'cypress/elements/enrichment-tool-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

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

  it('should display \'Enrichment Test\' button', () => {
    page.enrichmentTestButton.should('be.visible');
  });

  it('should display \'Share query\' button', () => {
    const shareQueryPage = new ShareQueryPage();
    shareQueryPage.button.should('be.visible');
  });

  it('should display \'Save query\' button', () => {
    const saveQueryPage = new SaveQueryPage();
    saveQueryPage.button.should('be.visible');
  });

  it('should display enrichment table after \'Enrichment Test\' button click', () => {
    const genesBlockPage = new GenesBlockPage();

    page.table.should('not.exist');

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    page.enrichmentTestButton.click();
    page.table.should('be.visible');
  });

  it('should display alert window after \'Enrichment Test\' button click when the gene symbols textarea is empty', () => {
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

  it('should display \'55\' and \'169\' in the affected person\'s observed column of LGDs and missense\'s rows respectively ' +
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

  it('should display \'0\' and \'2\' in the affected person\'s observed column of LGDs and missense\'s rows respectively ' +
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

describe('Enrichment tool data tests', () => {
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

  it('should display affected and unaffected variants based on gene symbol', () => {
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.geneSymbolsButton.click();

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    page.enrichmentTestButton.click();
    page.table.should('be.visible');
    
    (['LGDs', '363', '0', '0.05', '1.00', '27', '0',	'3.92e-3' , '1.00', '306', '0', '0.04', '1.00', '68', '0', '9.88e-3' ,'1.00']).forEach((el, index) => {
      page.findTableField('affected', 'LGDs', index).should('have.text', el);
    });
    (['Missense', '1,510', '1', '0.22',	'0.197', '149', '0',	'0.02',	'1.00',	'1,307',	'1',	'0.19',	'0.173', '246', '0', '0.04', '1.00']).forEach((el, index) => {
      page.findTableField('affected', 'Missense', index).should('have.text', el);
    });

    page.selectorTableRow('affected').should('have.text', 'affected F:341  M:2166  U: -');
    page.selectorTableRow('unaffected').should('have.text', 'unaffected F:1011  M:899  U: -');
  });

  it('should perform enrichment test based on gene sets', () => { // TODO: unaffected tests
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.geneSetsButton.click();

    page.geneSetsInputField.type('autism').then(option => {
      cy.get('div.dropdown-menu').should('contain.text', 'PNAS 2015');
      cy.get('span').contains('PNAS 2015').click();
      page.geneSetsVariantsCount.should('have.text', 'Count: 239');
    });
    page.enrichmentTestButton.click();
    ['LGDs', '363', '97', '12.87', '2.48e-55', '27', '22', '0.96', '8.48e-28', '306', '78', '10.85', '3.29e-43', '68', '29', '2.41', '3.11e-24'].forEach((el, index) => {
      page.findTableField('affected', 'LGDs', index).should('have.text', el);
    });


    page.geneSetsColletionDropdown.select('Denovo');
    page.geneSetsInputField.type('LGDs').then(option => {
      cy.get('div.dropdown-menu').should('contain.text', 'LGDs (363)');
      cy.get('span').contains('LGDs (363)').click();
      page.geneSetsVariantsCount.should('have.text', 'Count: 363');
    });
    page.enrichmentTestButton.click();
    ['LGDs', '363', '363', '13.67', '0.00', '27', '27', '1.02', '3.53e-39', '306', '306', '11.52', '0.00', '68', '68', '2.56', '1.43e-97'].forEach((el, index) => {
      page.findTableField('affected', 'LGDs', index).should('have.text', el);
    });

    cy.get('input#iossifov_2014-checkbox-affected').click();
    page.findErrorAlertInComponent('gpf-gene-sets').contains('Please select a gene');

    cy.get('input#iossifov_2014-checkbox-unaffected').click();
    page.geneSetsInputField.type('LGDs').then(option => {
      cy.get('div.dropdown-menu').should('contain.text', 'LGDs (176)');
      cy.get('span').contains('LGDs (176)').click();
      page.geneSetsVariantsCount.should('have.text', 'Count: 176');
    });
    page.enrichmentTestButton.click();
    ['LGDs', '363', '8', '6.13', '0.4108', '27', '1', '0.46', '0.3686', '306', '7', '5.17', '0.3708', '68', '1', '1.15', '1.00'].forEach((el, index) => {
      page.findTableField('affected', 'LGDs', index).should('have.text', el);
    });
  });

  it('should display affected and unaffected variants based on gene symbol and select models', () => {
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.geneSymbolsButton.click();

    genesBlockPage.geneSymbolsTextarea.type('CAMSAP1');
    
    // TODO data based test in columns/rows
    page.enrichmentModelsBlock.then(() => {
      cy.get('a#ngb-nav-4').click();
    });

    page.enrichmentTestButton.click();
    page.table.should('be.visible');

    /*['LGDs', '392', '0', '0.06', '1.00', '27', '0', '3.92e-3', '1.00', '321', '0', '0.05', '1.00', '71', '0', '0.01', '1.00'].forEach((el, index) => {
      page.findTableField('affected', 'LGDs', index).should('have.text', el);
    });*/
    compare_data('gene_symbol_without_model_LGDs', 'affected', 'LGDs');

    page.enrichmentModelsSelector('background').select('samocha_background_model');
    page.enrichmentModelsSelector('counting').select('enrichment_gene_counting');
    page.enrichmentTestButton.click();

    // TODO test more values

    /*['LGDs', '363', '0', '0.03', '1.00', '27', '0', '1.89e-3', '1.00', '306', '0', '0.02', '1.00', '68', '0', '3.45e-3', '1.00'].forEach((el, index) => {
      page.findTableField('affected', 'LGDs', index).should('have.text', el);
    });*/ //experimental below
    compare_data('gene_symbol_and_models_LGDs', 'affected', 'LGDs');

  });
});

class data_model {
  public set_name: string;
  public data: Array<string>;

  constructor(set_name, data) {
    this.set_name = set_name;
    this.data = data;
  }
}
const data = [
  new data_model('gene_symbol_and_models_LGDs' ,['LGDs', '363', '0', '0.03', '1.00', '27', '0', '1.89e-3', '1.00', '306', '0', '0.02', '1.00', '68', '0', '3.45e-3', '1.00']),
  new data_model('gene_symbol_without_model_LGDs', ['LGDs', '392', '0', '0.06', '1.00', '27', '0', '3.92e-3', '1.00', '321', '0', '0.05', '1.00', '71', '0', '0.01', '1.00'])
] ;

function compare_data(set_name: string, affected: string, type: string) {
  const page = new EnrichmentToolPage();
  const dataset = data.filter(item => item.set_name === set_name);
  dataset.forEach(el => {
    el.data.forEach((el, index) => {
      page.findTableField(affected, type, index).should('have.text', el);
    });
  });
}