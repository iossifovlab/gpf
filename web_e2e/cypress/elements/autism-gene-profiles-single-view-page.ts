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
    return cy.get('table.datasets-table > tbody >  tr#' + id + '> td').eq(type);
  }

  get externalLinksTable() {
    return cy.get('#external-links');
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

  compareData(data: any) {
    const page = new AutismGeneProfilesSingleView();
  
    if(data.hasOwnProperty('data')) {

      data.data.forEach(value => {
        [0, 1].forEach(tab => { // tables
          page.genomicScoresTable.eq(tab).each(name => {
            cy.wrap(name).within(table => {
              cy.wrap(table).get('td').not('.ng-star-inserted').each((element, id) => {
                if(element.text() === value['name']) {
                  expect(element.text()).to.equal(value['name']);
                  cy.wrap(table).get('td.ng-star-inserted').eq(id).within(scores => {
                    cy.wrap(scores).get('g > text.small').should('have.text', value['value']);
                  });
                }
              });
            });
          });
        })
      });
    }
    

    if(data.hasOwnProperty('statistics')) {
      ['autism_gene_sets', 'relevant_gene_sets'].forEach(element => {
        let pg: Cypress.Chainable<JQuery<HTMLElement>> = null;
        switch(element) {
          case 'autism_gene_sets': {
            if(!data.statistics.hasOwnProperty('autism_gene_sets')) {
              break;
            }
            pg = page.geneAutismGeneSetsTable;
            break;
          }
          case 'relevant_gene_sets': {
            if(!data.statistics.hasOwnProperty('relevant_gene_sets')) {
              break;
            }
            pg = page.geneRelevantGeneSetsTable;
            break;
          }
          default: {
            pg = null;
            break;
          }
        }

        if(pg !== null) {
          pg.within(table => {
            cy.wrap(table).get('tr').each((el, index) => {
              cy.wrap(el).within(col => {
                cy.wrap(col).get('td').eq(0).should('have.text', data['statistics'][element][index]['name']);
              });
              if(data['statistics'][element][index]['value'] === true) {
                cy.wrap(el).within(col => {
                  cy.wrap(col).get('td').eq(1).should('have.length', 1);
                });
              }
            });
          });
        }
      });
    
      if(data.statistics.hasOwnProperty('study')) {
        data.statistics.study.variant_ids.forEach((id, index) => {
          console.log(index);
          this.datasetsTableColumn(id, 0).should('have.text', data.statistics.study.variant_statistics[index]);
          this.datasetsTableColumn(id, 1).should('have.text', data.statistics.study.affected[index]);
          this.datasetsTableColumn(id, 2).should('have.text', data.statistics.study.unaffected[index]);
        });
      }
    }
  }
}
