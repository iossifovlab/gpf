import { EnrichmentToolPage } from 'cypress/elements/enrichment-tool-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { GenesWeights } from 'cypress/elements/genes-weights';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

import * as YAML from 'yaml';

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

describe.only('Enrichment tool data tests', () => {
  const page = new EnrichmentToolPage();
  let data1: object;

  before(() => {
    cy.readFile(Cypress.env().externalReferenceDataFilePath, { timeout: 5000 }).then(text => {
      data1 = YAML.parse(text);
    });

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

    parseOptions(getDataset('gene_symbol_CAMSAP1').request);
    page.enrichmentTestButton.click();
    page.table.should('be.visible');
    
    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_CAMSAP1').data);
    });
    cy.wrap(page.getTableData('affected', 'Missense')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_CAMSAP1', 'Missense').data);
    });

    page.selectorTableRow('affected').should('have.text', 'affected F:341  M:2166  U: -');
    page.selectorTableRow('unaffected').should('have.text', 'unaffected F:1011  M:899  U: -');
  });

  it('should perform enrichment test based on gene sets', () => { // TODO: unaffected tests
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.geneSetsButton.click();

    parseOptions(getDataset('gene_symbol_pnas_2015_set').request);
    page.enrichmentTestButton.click();

    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_pnas_2015_set').data);
    });
    cy.wrap(page.getTableData('affected', 'Missense')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_pnas_2015_set', 'Missense').data);
    });
    cy.wrap(page.getTableData('unaffected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_pnas_2015_set', 'LGDs', 'unaffected').data);
    });

    parseOptions(getDataset('gene_symbols_iossifov_affected').request);
    page.enrichmentTestButton.click();
    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbols_iossifov_affected').data);
    });
    cy.wrap(page.getTableData('affected', 'Missense')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbols_iossifov_affected', 'Missense').data);
    });

    parseOptions(new RequestOptions('gene_sets', {
      implicit: true,
      denovo_collection_sets: [
        {
          study_type: 'iossifov_2014: Affected Status',
          affected: false,
          unaffected: false
        }, 
      ]
    }, null));
    page.findErrorAlertInComponent('gpf-gene-sets').contains('Please select a gene');

    parseOptions(new RequestOptions('gene_sets', {
      set: 'Denovo',
      study: 'LGDs (176)',
      denovo_collection_sets: [
        {
          study_type: 'iossifov_2014: Affected Status',
          affected: false,
          unaffected: true
        }, 
      ]
    }, ['default']));
    page.enrichmentTestButton.click();
    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_iossifov_unaffected').data);
    });
  });

  it('should display affected and unaffected variants based on gene symbol and select models', () => {

    parseOptions(getDataset('gene_symbol_without_model_LGDs').request);
    page.enrichmentTestButton.click();
    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_without_model_LGDs').data);
    });

    parseOptions(getDataset('gene_symbol_and_models_LGDs').request);
    page.enrichmentTestButton.click();

    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_symbol_and_models_LGDs').data);
    });
  });

  it('should move gene weights slider', () => { /// inconsistent data model
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.geneWeightsButton.click();

    cy.intercept('POST', '/gpf/api/v3/gene_weights/partitions', {
      body:{
        left: {count: 0, percent: 0},
        mid: {count: 910, percent: 1},
        right: {count: 0, percent: 0}
      }
    }).as('WeightsOptions');
    parseOptions(getDataset('gene_weights_sfari_gene_score_right').request);
    cy.wait('@WeightsOptions');
    cy.wait('@WeightsOptions'); // That's bug from the GPFJS site, many excess requests are made with gene weights
    cy.wait(1000); // fix state bug
    page.enrichmentTestButton.click();

    cy.wrap(page.getTableData('affected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_weights_sfari_gene_score_right').data);
    });

    parseOptions(getDataset('gene_weights_sfari_gene_score_left', 'LGDs', 'unaffected').request);
    cy.wait('@WeightsOptions'); // That's bug from the GPFJS site, many excess requests are made with gene weights
    cy.wait(1000); // fix state bug
    page.enrichmentTestButton.click();

    cy.wrap(page.getTableData('unaffected')).then(() => {
      cy.get('@tableData').should('deep.equal', getDataset('gene_weights_sfari_gene_score_left', 'LGDs', 'unaffected').data);
    });
  });
});

class RequestOptions {
  public mode: string;
  public options: JSON;
  public modelsSelected?: string[];

  constructor(mode, options, modelsSelected: string[]) {
    this.mode = mode;
    this.options = options;
    this.modelsSelected = modelsSelected;
  }
}

const data = [
  {
    id: 'gene_symbol_CAMSAP1',
    affectedStatus: 'affected',
    request: new RequestOptions(
      'gene_symbols',
      {gene_symbols: 'CAMSAP1'},
      null
    ),
    data: ['LGDs', '363', '0', '0.05', '1.00', '27', '0', '3.92e-3', '1.00', '306', '0', '0.04', '1.00', '68', '0', '9.88e-3', '1.00']
  },
  {
    id: 'gene_symbol_CAMSAP1',
    affectedStatus: 'affected',
    request: new RequestOptions(null, null, null),
    data: ['Missense', '1,510', '1', '0.22', '0.197', '149', '0', '0.02', '1.00', '1,307', '1', '0.19', '0.173', '246', '0', '0.04', '1.00']
  },
  {
    id: 'gene_symbol_and_models_LGDs',
    affectedStatus: 'affected',
    request: new RequestOptions('gene_symbols', {
      gene_symbols: 'CAMSAP1'
    }, ['samocha_background_model', 'enrichment_gene_counting']),
    data: ['LGDs', '363', '0', '0.03', '1.00', '27', '0', '1.89e-3', '1.00', '306', '0', '0.02', '1.00', '68', '0', '3.45e-3', '1.00']
  },
  {
    id: 'gene_symbol_without_model_LGDs',
    affectedStatus: 'affected',
    request: new RequestOptions('gene_symbols', {
      gene_symbols: 'CAMSAP1'
    }, ['coding_len_background_model', 'enrichment_events_counting']),
    data: ['LGDs', '392', '0', '0.06', '1.00', '27', '0', '3.92e-3', '1.00', '321', '0', '0.05', '1.00', '71', '0', '0.01', '1.00']
  },
  {
    id: 'gene_symbols_iossifov_affected',
    affectedStatus: 'affected',
    request: new RequestOptions('gene_sets', {
      set: 'Denovo',
      study: 'LGDs (363)',
      denovo_collection_sets: [
        {
          study_type: 'iossifov_2014: Affected Status',
          affected: true,
          unaffected: false
        }, 
      ]
    }, ['samocha_background_model', 'enrichment_gene_counting']),
    data: ['LGDs', '363', '363', '7.81', '0.00', '27', '27', '0.58', '0.00', '306', '306', '6.75', '0.00', '68', '68', '1.06', '0.00']
  },
  {
    id: 'gene_symbols_iossifov_affected',
    affectedStatus: 'affected',
    request: new RequestOptions(null, null, null),
    data: ['Missense', '1,510', '75', '54.72', '0.0107', '149', '16', '5.40', '0.0003', '1,307', '67', '47.28', '0.0079', '246', '12', '7.44', '0.152']
  },
  {
    id: 'gene_symbol_iossifov_unaffected',
    affectedStatus: 'affected',
    request: new RequestOptions(null, null, null),
    data: ['LGDs', '363', '8', '6.13', '0.4108', '27', '1', '0.46', '0.3686', '306', '7', '5.17', '0.3708', '68', '1', '1.15', '1.00']
  },
  {
    id: 'gene_symbol_pnas_2015_set',
    affectedStatus: 'affected',
    request: new RequestOptions('gene_sets', {
      set: 'Main',
      study: 'autism candidates from Iossifov',
    }, null),
    data: ['LGDs', '363', '97', '12.87', '2.48e-55', '27', '22', '0.96', '8.48e-28', '306', '78', '10.85', '3.29e-43', '68', '29', '2.41', '3.11e-24']
  },
  {
    id: 'gene_symbol_pnas_2015_set',
    affectedStatus: 'affected',
    request: new RequestOptions(null, null, null),
    data: ['Missense', '1,510', '114', '53.56', '1.71e-13', '149', '34', '5.28', '3.90e-18', '1,307', '100', '46.36', '2.30e-12', '246', '22', '8.73', '7.94e-5']
  },
  {
    id: 'gene_symbol_pnas_2015_set',
    affectedStatus: 'unaffected',
    request: new RequestOptions(null, null, null),
    data: ['LGDs', '176', '4', '6.24', '0.537', '3', '0', '0.11', '1.00', '84', '2', '2.98', '0.7719', '94', '2', '3.33', '0.7763']
  }, {
    id: 'gene_weights_sfari_gene_score_right',
    affectedStatus: 'affected',
    request: new RequestOptions('gene_weights', {
      scroll: [{
        position: 'right',
        value: 150
      }]
    }, null),
    data: ['LGDs', '363', '107', '20.74', '5.86e-46', '27', '27', '1.54', '2.73e-34', '306', '82', '17.48', '2.36e-32', '68', '36', '3.89', '7.20e-27']
  }, {
    id: 'gene_weights_sfari_gene_score_left',
    affectedStatus: 'unaffected',
    request: new RequestOptions('gene_weights', {
      scroll: [{
        position: 'left',
        value: 150
      }]
    }, null),
    data: ['LGDs', '176', '8', '7.27', '0.7043', '3', '0', '0.12', '1.00', '84', '6', '3.47', '0.1632', '94', '2', '3.88', '0.4428']
  }
];

function parseOptions(request: RequestOptions) {
  const page = new EnrichmentToolPage();
  const genesBlockPage = new GenesBlockPage();
  const weights = new GenesWeights();

  switch(request.mode) {
    case 'gene_symbols': {
      genesBlockPage.geneSymbolsButton.click();
      genesBlockPage.geneSymbolsTextarea.clear().type(request.options['gene_symbols']);
      break;
    }
    case 'gene_sets': {
      if(request.options['implicit'] === undefined || request.options['implicit'] === false) {
        genesBlockPage.geneSetsButton.click();
      }
      if(request.options['set'] !== undefined) {
        page.geneSetsColletionDropdown.select(request.options['set']);
      }

      if((request.options['set'] === 'Denovo' && request.options['set'] !== undefined) || request.options['implicit'] === true) {
        request.options['denovo_collection_sets'].forEach(element => {
          //checkboxes exclusive for denovo
          cy.get('ngb-accordion > div').within(() => {
            cy.get('span.dropdown-toggle').contains(element['study_type']).click().parents('.card.ng-star-inserted').within(() => {
              cy.get('label > input[type="checkbox"]').uncheck({force: true});
              if(element['affected'] === true) {
                cy.get('label').contains('affected').click({force: true});
              }
              if(element['unaffected'] === true) {
                cy.get('label').contains('unaffected').click({force: true});
              }
            });        
          });
        });
      }

      if (request.options['study'] !== undefined) {
        page.geneSetsInputField.clear().type(request.options['study']).then(() => {
          cy.get('input#search-box').click();
          cy.get('div.dropdown-menu.show').should('be.visible').click().should('contain.text', request.options['study']).get('span').contains(request.options['study']).click();
        });
      }

      break;
    }
    case 'gene_weights': {
      genesBlockPage.geneWeightsButton.click();
      genesBlockPage.genesWeightsPanel.within(panel => {
        if(request.options.hasOwnProperty('weights')) {
          cy.wrap(panel).get('select.form-control').select(request.options['weights']);
        }
      });
      if(request.options.hasOwnProperty('scroll')) {
        request.options['scroll'].forEach(element => {
          weights.moveSlider(element['position'], element['value'], 0);
        });
      } 
      if(request.options.hasOwnProperty('step')) {
        request.options['step'].forEach(element => {
          if(element.hasOwnProperty('position') && element.hasOwnProperty('value')) {
            weights.setInputFieldValue(element['position'], element['value']);
          }
          if(element.hasOwnProperty('position') && element.hasOwnProperty('click')) {
            weights.clickInputField(element['position'], element.click['which'], element.click['times']);
          }
        });
      }
      break;
    } default: {
      throw new Error('Unknown mode selected: ' + request.mode);
    }
  }
  if (request.modelsSelected !== null && request.modelsSelected.length === 2) {
    page.enrichmentModelsBlock.within(() => {
      cy.get('a#ngb-nav-4').click();
    });
    request.modelsSelected.forEach((element, index) => {
      page.enrichmentModelsSelect((index === 0) ? 'background' : 'counting', element);
    });
  } else if (request.modelsSelected !== null && request.modelsSelected[0] === 'default' && request.modelsSelected.length === 1) {
    page.enrichmentModelsBlock.within(() => {
      cy.get('a#ngb-nav-3').click();
    });
  }
}

function getDataset(id: string, type: string = 'LGDs', affected: string = 'affected') {
  return data.filter(match => {
    return (match.id === id && match.data[0] === type)
  }).find(match => { return (match.affectedStatus === affected) });
}
