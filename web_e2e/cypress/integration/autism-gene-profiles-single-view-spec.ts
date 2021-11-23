import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { BasePage, sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles single view tests', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display header', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.header.should('be.visible');
    page.header.should('have.text', 'CHD8');
  });

  it('should display the autism scores table', () => {
    page.autismScoresTable.should('be.visible');
    page.autismScoresTable.find('th').should('have.text', 'Autism Scores');
    page.autismScoresTable.find('tr').should('have.length', 1);
  });

  it('should display the protection scores table', () => {
    page.protectionScoresTable.should('be.visible');
    page.protectionScoresTable.find('th').should('have.text', 'Protection Scores');
    page.protectionScoresTable.find('tr').should('have.length', 4);
  });

  it('should display the single scores markers', () => {
    page.singleScoreMarkers.should('have.length', 5);
  });

  it('should display the autism gene sets table', () => {
    page.geneAutismGeneSetsTable.should('be.visible');
    page.geneAutismGeneSetsTable.find('th').should('have.text', 'Autism Gene Sets');
    page.geneAutismGeneSetsTable.find('tr').should('have.length', 2);
  });

  it('should display the relevant gene sets table', () => {
    page.geneRelevantGeneSetsTable.should('be.visible');
    page.geneRelevantGeneSetsTable.find('th').should('have.text', 'Relevant Gene Sets');
    page.geneRelevantGeneSetsTable.find('tr').should('have.length', 4);
  });

  it('should display the datasets table', () => {
    page.datasetsTable.should('be.visible');
    page.datasetsTable.find('th').first().should('have.text', 'iossifov_2014');
    page.datasetsTable.find('tr').should('have.length', 5);
  });
});

describe('Autism gene profiles single view links tests', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display gene browser link', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.geneBrowserLink.should('be.visible');
    page.geneBrowserLink.should('have.text', 'View CHD8 in the Gene Browser');
  });

  it('should display UCSC link', () => {
    page.UCSCLink.should('be.visible');
    page.UCSCLink.should('have.text', 'UCSC genome browser');
  });

  it('should display GeneCards link', () => {
    page.geneCardsLink.should('be.visible');
    page.geneCardsLink.should('have.text', 'GeneCards');
  });

  it('should display Pubmed link', () => {
    page.pubmedLink.should('be.visible');
    page.pubmedLink.should('have.text', 'Pubmed');
  });

  it('should have the correct href for the gene browser link', () => {
    page.header.invoke('text').then((headerText) => {
      const baseUrl = Cypress.config().baseUrl;
      const headerName = headerText;
      const geneBrowserUrl = `${baseUrl}datasets/ALL_genotypes/gene-browser/${headerName}`;
      page.geneBrowserLink.should('have.prop', 'href').and('equal', geneBrowserUrl)
    });
  });

  it('should have the correct href for the UCSC link', () => {
    const UCSCLink = 'https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr14%3A21853353-21905457';
    page.UCSCLink.should('have.prop', 'href').and('equal', UCSCLink)
  });

  it('should have the correct href for the GeneCards link', () => {
    const geneCardsLink = 'https://www.genecards.org/cgi-bin/carddisp.pl?gene=CHD8';
    page.geneCardsLink.should('have.prop', 'href').and('equal', geneCardsLink)
  });

  it('should have the correct href for the Pubmed link', () => {
    const pubmedLink = 'https://pubmed.ncbi.nlm.nih.gov/?term=CHD8%20AND%20(autism%20OR%20asd)';
    page.pubmedLink.should('have.prop', 'href').and('equal', pubmedLink)
  });
  +
/*
  it('should display SFARI link when is contained in the list', () => {
  });
  // add tests for SFARI link - it had a specific condition in order to be displayed,
  // see if that logic works
  // it('should display SFARI link when ... and not display it when ...', () => {
  // });
  // it('should have the correct href for the SFARI link', () => {
  // }); */

  it('should load more genes when scrolling', () => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);

    cy.get('.table tr').should('have.length.above', 5);
    cy.get('.table').find('tr').its('length').then(value => {
      cy.scrollTo('bottom');
      cy.get('.table tr').should('have.length.above', value);
    });
  });

  it('should have proper single view data', () => {
    //page.cleanup();
    //page.navigateToHome();
    //page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=GRIN2B&sortBy=autism_gene_sets_rank&order=desc').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');
    //autismGeneProfilesTablePage.allTableCells.first().click();
    cy.get('.genomic-scores-table').should('be.visible');
    page.geneSymbol.should('have.text', gene_data.gene_symbols);


    let gene_data_ = {
      gene_symbols: '',
      autism_scores: [
        { name:'', value: null }
      ], protection_scores: [
        { name: '', value: null },
      ],
      statistics: {
        autism_gene_sets: [
          { name: '', value: null },
        ], relevant_gene_sets: [
          { name: '', value:  null },
        ], study: {
          variant_statistics: [''],
          variant_ids: [''],
          affected: [''],
          unaffected: ['']
        }
      }
    }

    //page.compareData(gene_data);
    /*page.getAutismScores(page);
    page.getProtectionScores(page);
    page.getAutismGeneSets(page);
    page.getRelevantGeneSets(page);
    page.getStudyTable(page, 0);*/
    //page.compareData(page);
  });

  it('should compare all data in single view', () => {
    const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');
    page.compareData(page);

    cy.get('@result').then(value => {
      cy.wrap(value).should('deep.equal', gene_data);
    });
    //or cy.intercept to wait asynchronous calls
  });

  it('should compare study table in single view', () => { // could be used describe in order to skip writing the lines from 189 to 196
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
    const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=GRIN2B&sortBy=autism_gene_sets_rank&order=desc').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');
    
    page.getStudyTable(page, 0);
    cy.get('@study_results').then(value => {
      cy.wrap(value).should('deep.equal', gene_data.statistics.study);
    });
  });
});

describe('Single view study table', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  it.skip('should test redirect logic', () => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);

    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=GRIN2B&sortBy=autism_gene_sets_rank&order=desc').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');

    page.datasetsTable.within(table => {
      cy.wrap(table).get('td').each(el => {
        if(el.text() === '' || el.text() === '–') {
  
        } else {
          cy.wrap(el).parent().invoke('attr', 'id').then(id => {
            //console.log(id); // id could be useful for fetching data from the data array
            //gene_data.statistics.study[id];
          });

          cy.wrap(el).click();
          cy.intercept({
            method: 'POST',
            url: '/gpf/api/v3/query_state/save'
          }, req => {
            console.log(req); // query body
          }).as('query');
          //intercept request to get the response body(contains the url for the request)
          cy.get('@query').then(req => {
            if(req !== null) {
              let baseUrl = Cypress.config().baseUrl;
              if(baseUrl.endsWith('/')) {
                baseUrl = baseUrl.slice(0, -1);
              }
              const pg = new BasePage();
              pg.preserveLogin();
              cy.visit(`${baseUrl}/load-query/${req.response.body.uuid}`);
              //const pg = new BasePage();
              cy.wait(5000);
              //pg.login('admin@iossifovlab.com', 'secret');
              cy.wait(15000);
              console.log(req.response.body.uuid);
              //cy.visit(Cypress.config().baseUrl + '/load-query/' + req.response.body);
              //compare the genotype options with a new data array(data_wrapper: [{}])
            }
          }); // can potentially get the data from the query body and compare it to the response URL(redirects to genotype browser)
        }
      });
    });
  });
});

// seperate data -> autism scores/ protection
const gene_data: any = {
  gene_symbols: 'GRIN2B',
  autism_scores: [
    { name:'SFARI_gene_score', value: 1 }
  ], protection_scores: [ // sfari_score: 
    { name: 'RVIS_rank', value: 174.5 },  // rvis_rank: 
    { name: 'LGD_rank', value: 85.5 }, // lgd_rank:
    { name: 'pLI_rank', value: 400 }, // pli_rank: 
    { name: 'pRec_rank', value: 17792 } // prec_rank: 
  ],
  statistics: {
    autism_gene_sets: [
      { name: 'autism candidates from Iossifov PNAS 2015', value: true },
      { name: 'autism candidates from Sanders Neuron 2015', value: true }
    ], relevant_gene_sets: [
      { name: 'CHD8 target genes', value:  false },
      { name: 'chromatin modifiers', value:  false },
      { name: 'essential genes', value:  true },
      { name: 'FMRP Darnell', value:  true }
    ], study: [
      // title
      {
        variant_statistics: "LGDs", variant_ids: "denovo_lgds", affected: "3 (1.197)", unaffected: "–"
      },
      {
        variant_statistics: "missense", variant_ids: "denovo_missense", affected: "1 (0.399)", unaffected: "–"
      },
      {
        variant_statistics: "intron", variant_ids: "denovo_intron", affected: "–", unaffected: "–"
      }
    ]
  }
}

//describe('')
/*
const gene_data = {
  gene_symbols: 'GRIN2B',
  autism_scores: [
    { name:'SFARI_gene_score', value: 1 }
  ], protection_scores: [ // sfari_score: 
    { name: 'RVIS_rank', value: 174.5 },  // rvis_rank: 
    { name: 'LGD_rank', value: 85.5 }, // lgd_rank:
    { name: 'pLI_rank', value: 400 }, // pli_rank: 
    { name: 'pRec_rank', value: 17792 } // prec_rank: 
  ],
  statistics: {
    autism_gene_sets: [
      { name: 'autism candidates from Iossifov PNAS 2015', value: true },
      { name: 'autism candidates from Sanders Neuron 2015', value: true }
    ], relevant_gene_sets: [
      { name: 'CHD8 target genes', value:  false },
      { name: 'chromatin modifiers', value:  true },
      { name: 'essential genes', value:  true },
      { name: 'FMRP Darnell', value:  true }
    ], study: {
      // title
      variant_statistics: ['LGDs', 'missense', 'intron'],
      variant_ids: ['denovo_lgds', 'denovo_missense', 'denovo_intron'],
      affected: ['3 (1.197)', '1 (0.399)', '–'],
      unaffected: ['–', '–', '–']
    }
  }
}
*/

//it = > get(variant_stat).should('');
/*
const sfari_genes = [
  'ABCA7',
  'ACE',
  'ACHE',
  'ARHGEF10',
  'BICRA',
  'BICDL1',
  'BRINP3',
  'BST1'
];
*/
data_wrapper: [{
  "phenoToolMeasureState": {
      "measureId": "",
      "normalizeBy": []
  },
  "genomicScoresBlockState": {
      "genomicScores": []
  },
  "personFiltersState": {
      "familyFilters": [],
      "personFilters": []
  },
  "studyFiltersBlockState": {
      "studyFilters": []
  },
  "familyTypeFilterState": {
      "familyTypes": [
          "trio",
          "quad",
          "multigenerational",
          "simplex",
          "multiplex",
          "other"
      ]
  },
  "pedigreeSelectorState": {
      "id": "status",
      "checkedValues": [
          "affected"
      ]
  },
  "enrichmentModelsState": {
      "enrichmentBackgroundModel": "",
      "enrichmentCountingModel": ""
  },
  "geneWeightsState": {
      "geneWeight": null,
      "rangeStart": 0,
      "rangeEnd": 0
  },
  "geneSetsState": {
      "geneSetsTypes": null,
      "geneSetsCollection": null,
      "geneSet": null
  },
  "studyTypesState": {
      "studyTypes": [
          "we"
      ]
  },
  "regionsFiltersState": {
      "regionsFilters": []
  },
  "familyIdsState": {
      "familyIds": []
  },
  "geneSymbolsState": {
      "geneSymbols": [
          "GRIN2B"
      ]
  },
  "presentInParentState": {
      "presentInParent": [
          "neither"
      ],
      "rarityType": "all",
      "rarityIntervalStart": 0,
      "rarityIntervalEnd": 1
  },
  "presentInChildState": {
      "presentInChild": [
          "proband only",
          "proband and sibling",
          "sibling only"
      ]
  },
  "personIdsState": {
      "personIds": []
  },
  "inheritancetypesState": {
      "inheritanceTypes": []
  },
  "genderState": {
      "genders": [
          "male",
          "female",
          "unspecified"
      ]
  },
  "effecttypesState": {
      "effectTypes": []
  },
  "varianttypesState": {
      "variantTypes": []
  },
  "datasetId": "iossifov_2014"
}]