import { any } from 'cypress/types/bluebird';
import { AutismGeneProfilesTable } from './autism-gene-profiles-table-page';
import { BasePage } from './utils';

export class AutismGeneProfilesSingleView extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profile-single-view');
  }

  get header() {
    return cy.get('gpf-autism-gene-profile-single-view h2');
  }

  get geneBrowserLink() {
    return cy.get('#gene-browser-link');
  }

  get UCSCLink() {
    return cy.get('a.link-external-page').contains('UCSC genome browser');
  }

  get geneCardsLink() {
    return cy.get('a.link-external-page').contains('GeneCards');
  }

  get pubmedLink() {
    return cy.get('a.link-external-page').contains('Pubmed');
  }

  get autismScoresTable() {
    return cy.get('#autism_scores');
  }

  get protectionScoresTable() {
    return cy.get('#protection_scores');
  }

  get singleScoreMarkers() {
    return cy.get('.single-score-marker');
  }

  get geneAutismGeneSetsTable() {
    return cy.get('#autism_gene_sets');
  }

  get genomicScoresTable() {
    return cy.get('table.genomic-scores-table');
  }

  get autismGeneToolAllView() {
    return cy.get('a#ngb-nav-0.nav-link');
  }

  get geneRelevantGeneSetsTable() {
    return cy.get('#relevant_gene_sets');
  }

  get datasetsTable() {
    return cy.get('.datasets-table');
  }

  datasetsTableColumn(id: string, type: number) {
    return cy.document().its('body').find('table.datasets-table > tbody >  tr#' + id + ' > td').eq(type);
  }

  get externalLinksTable() {
    return cy.get('#external-links');
  }

  get geneSymbol() {
    return cy.get('gpf-autism-gene-profile-single-view > div > h2');
  }

  openSingleView(gene: string, force: boolean = false) {
    const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
    const page = new AutismGeneProfilesSingleView();
    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type(gene);
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=' + gene + '**').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView(gene, force);
  }

  getView(name: string, force = true) {
    cy.get('nav > li > a > span').not('.close').each(nav => {
      cy.wrap(nav).eq(0).then(el => {
        if(el.text() === name) {
          cy.wrap(el).click();
          return false;
        } else {
          if(force === true) {
            cy.wrap(el).parent().children().eq(1).click();
          }
          return false;
        }
      });
    });
  }

  getGeneSymbols(): any {
    cy.get('gpf-autism-gene-profile-single-view > div> h2').then(symbols => {
      cy.wrap(symbols.text()).as('geneSymbols');
    });
  }

  getGenomicScores(): any {
    let genomicScores: any = [];

    cy.get('div.ng-star-inserted > :nth-child(3) > table').each((table_iteration, index) => {
      genomicScores[index] = {
        category: '', name: '', scores: []
      }

      cy.wrap(table_iteration).within(table => {

        cy.wrap(table).invoke('attr', 'id').then(id => {
          genomicScores[index].category = id;
        });

        cy.wrap(table).get('th').then(name => {
          genomicScores[index].name = name.text();
        });

        cy.wrap(table).get('tr').each((table_row, row_index) => {
          genomicScores[index].scores[row_index] = {
            name: '', value: null
          }

          cy.wrap(table_row).within(row => {
            cy.wrap(row).get('td').not('.ng-star-inserted').then(score_name => {
              genomicScores[index].scores[row_index].name = score_name.text();
            });

            cy.wrap(row).get('td.ng-star-inserted').within(score_values => {
              cy.wrap(score_values).get('g > text.small').then(score => {
                genomicScores[index].scores[row_index].value = parseFloat(score.text());
              });
            });
          });
        });
      });
    });

    cy.wrap(genomicScores).as('genomicScores');
    return genomicScores;
  }

  getGeneSets(): any {
    let geneSets: any = [
    ];

    cy.get('div.ng-star-inserted > :nth-child(4) > table').each((table_iteration, index) => {
      cy.wrap(table_iteration).within(table => {

        geneSets[index] = {
          id: null, name: null, scores: [
          ] 
        };

        cy.wrap(table).invoke('attr', 'id').then(id => {
          geneSets[index]['id'] = id; // sets the id
        });
        cy.wrap(table).get('th').then(tableName => {
          geneSets[index]['name'] = tableName.text();
        });

        cy.wrap(table).get('tr').each((row, rowIndex) => {
          cy.wrap(row).within(el => {
            geneSets[index]['scores'][rowIndex] = {
              name: '',
              value: false
            };
    
            cy.wrap(el).get('td').eq(0).then(name => {
              geneSets[index]['scores'][rowIndex]['name'] = name.text();
            });
            cy.wrap(el).get('td').eq(1).then(value => {
              if(value.text().length === 1) {
                geneSets[index]['scores'][rowIndex]['value'] = true;
              }
            });
          });
        });

      });
    });
    cy.wrap(geneSets).as('geneSets');
    return geneSets;
  }

  getDatasetData(): any {
    let datasets = [];

    cy.get('div.ng-star-inserted > :nth-child(5) > table').each((table_iterator,index) => {
      datasets[index] = {
        name: '', columns: [ ], rows: [
          {
            variant_statistics: '', variant_ids: '', affected: '', unaffected: ''
          }
        ]
      }
      cy.wrap(table_iterator).within(table => {
        cy.wrap(table).get('thead > :nth-child(1) > th > span').then(name => {
          datasets[index].name = name.text();
        });

        cy.wrap(table).get('thead > :nth-child(2) > th.ng-star-inserted').each((column, column_index) =>  {
          datasets[index].columns[column_index] = column.text();
        });

        cy.wrap(table).get('tbody > tr').each((table_row, table_index) =>{
          datasets[index].rows[table_index] = {
            variant_statistics: '', variant_ids: '', affected: '', unaffected: ''
          }
          cy.wrap(table_row).within(row => {
            cy.wrap(row).invoke('attr', 'id').then(id => {
              datasets[index].rows[table_index].variant_ids = id;
            });
            cy.wrap(row).get('td').not('.ng-star-inserted').then(name => {
              datasets[index].rows[table_index].variant_statistics = name.text();
            });
            cy.wrap(row).get('td').eq(1).then(affected => {
              datasets[index].rows[table_index].affected = affected.text();
            });
            cy.wrap(row).get('td').eq(2).then(unaffected => {
              datasets[index].rows[table_index].unaffected = unaffected.text();
            });
          });
        });
      });
    });

    cy.wrap(datasets).as('datasets');
    return datasets
  }

}
