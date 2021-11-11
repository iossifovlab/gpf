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
    return cy.get('table.table.datasets-table > tbody >  tr#' + id + ' > td').eq(type);
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

  getAutismScores(view: AutismGeneProfilesSingleView): any {
    let autism_scores = [];

    view.genomicScoresTable.eq(0).within(table => {
      cy.wrap(table).get('td').not('.ng-star-inserted').each((element, id) => {
        autism_scores[id] = {
          name: '',
          value: ''
        }

        autism_scores[id].name = { 
          name: element.text()
        }
        cy.wrap(table).get('td.ng-star-inserted').eq(id).then(scores => {
          cy.wrap(scores).get('g > text.small').then(value => {
            autism_scores[id].value = {
              value: value.text()
            }
          });
        });
      });
    });
    
    return autism_scores;
  }

  getProtectionScores(view: AutismGeneProfilesSingleView): any {
    let protection_scores = [];

    view.genomicScoresTable.eq(1).within(table => {
      cy.wrap(table).get('td').not('.ng-star-inserted').each((element, id) => {
        if(protection_scores[id] === undefined) {
          protection_scores[id] = {
            name: '',
            value: ''
          }
        }
        protection_scores[id].name = { 
          name: element.text()
        }
        cy.wrap(table).get('td.ng-star-inserted').eq(id).then(scores => {
          cy.wrap(scores).get('g > text.small').then(value => {
            protection_scores[id].value = {
              value: value.text()
            }
          });
        });
      });
    });
    
    return protection_scores;
  }

  getAutismGeneSets(view: AutismGeneProfilesSingleView): any {
    let autism_gene_sets = [];

    view.geneAutismGeneSetsTable.within(table => {
      cy.wrap(table).get('tr').each((row, index) => {
        cy.wrap(row).within(el => {
          autism_gene_sets[index] = {
            name: '',
            value: false
          };
  
          cy.wrap(el).get('td').eq(0).then(name => {
            autism_gene_sets[index].name = name.text();
          });
          cy.wrap(el).get('td').eq(1).then(value => {
            if(value.text().length === 1) {
              autism_gene_sets[index].value = true;
            }
          });
        });
      });
    });

    return autism_gene_sets;
  }

  getRelevantGeneSets(view: AutismGeneProfilesSingleView): any {
    let relevant_gene_sets = [];

    view.geneRelevantGeneSetsTable.within(table => {
      cy.wrap(table).get('tr').each((row, index) => {
        cy.wrap(row).within(el => {
          relevant_gene_sets[index] = {
            name: '',
            value: false
          };
  
          cy.wrap(el).get('td').eq(0).then(name => {
            relevant_gene_sets[index].name = name.text();
          });
          cy.wrap(el).get('td').eq(1).then(value => {
            if(value.text().length === 1) {
              relevant_gene_sets[index].value = true;
            }
          });
        });
      });
    });

    return relevant_gene_sets;
  }

  getStudyTable(view: AutismGeneProfilesSingleView, tableId: number): any {
    let  study = [];
    
    view.datasetsTable.eq(tableId).within(table => {
      cy.wrap(table).get('tbody > tr.ng-star-inserted').each((elv, num) => {
        cy.wrap(elv).within(el => {
          if(study[num] === undefined) {
            study[num] = {
              variant_statistics: '',
              variant_ids: '',
              affected: '',
              unaffected: '',
            }
          }
    
          cy.wrap(el).eq(num).invoke('attr', 'id').then(attr => {
            this.datasetsTableColumn(attr, 0).then(name => {
              study[num].variant_statistics = name.text();
            });
            this.datasetsTableColumn(attr, 1).then(affected => {
              study[num].affected = affected.text();
            });
            this.datasetsTableColumn(attr, 2).then(unaffected => {
              study[num].unaffected = unaffected.text();
            });
          });
        });
      });  
    });


    console.log(study);
    return study;
  }

  compareData(data: any) {
    const page = new AutismGeneProfilesSingleView();
  
    if(data.hasOwnProperty('data')) {
        [0, 1].forEach(tab => { // tables
          page.genomicScoresTable.eq(tab).each(name => {
            cy.wrap(name).within(table => {
              cy.wrap(table).get('td').not('.ng-star-inserted').each((element, id) => {
                const match = data.data.find(item => item.name === element.text());
                if(match !== undefined) {
                  expect(element.text()).to.equal(match.name);
                } else {
                  expect(element.text()).to.false;
                }
                console.log(match);/*
                if(element.text() === value['name']) {
                  expect(element.text()).to.equal(value['name']);
                  cy.wrap(table).get('td.ng-star-inserted').eq(id).within(scores => {
                    cy.wrap(scores).get('g > text.small').should('have.text', value['value']);
                  });
                }*/
              });
            });
          });
        })
    }

    if(data.hasOwnProperty('statistics')) {
      ['autism_gene_sets', 'relevant_gene_sets'].forEach(element => {
        let pg: Cypress.Chainable<JQuery<HTMLElement>> = null;
        let data_set = null;
        switch(element) {
          case 'autism_gene_sets': {
            if(!data.statistics.hasOwnProperty('autism_gene_sets')) {
              break;
            }
            pg = page.geneAutismGeneSetsTable;
            data_set = data.statistics.autism_gene_sets;
            break;
          }
          case 'relevant_gene_sets': {
            if(!data.statistics.hasOwnProperty('relevant_gene_sets')) {
              break;
            }
            pg = page.geneRelevantGeneSetsTable;
            data_set = data.statistics.relevant_gene_sets;
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
                if(data.statistics[element].hasOwnProperty(index)) {
                  data_set.forEach(set_name => {
                    cy.wrap(el).within(col => {
                        cy.wrap(col).get('td').eq(0).then(col_name => {
                          if(data['statistics'][element][index]['name'] === set_name.name && col_name.text() === set_name.name) {
                            cy.wrap(col_name).should('have.text', data['statistics'][element][index]['name']);
                          }
                        })
                    });
                    if(data['statistics'][element][index]['value'] === true && data['statistics'][element][index]['name'] === set_name.name) {
                      cy.wrap(el).within(col => {
                        cy.wrap(col).get('td').eq(1).should('have.length', 1);
                      });
                    }
                });
              }
            });
          });
        }
      });
    
      if(data.statistics.hasOwnProperty('study')) {
        data.statistics.study.variant_ids.forEach((id, index) => {
          this.datasetsTableColumn(id, 0).should('have.text', data.statistics.study.variant_statistics[index]);
          this.datasetsTableColumn(id, 1).should('have.text', data.statistics.study.affected[index]);
          this.datasetsTableColumn(id, 2).should('have.text', data.statistics.study.unaffected[index]);
        });
      }
    }
  }
}
