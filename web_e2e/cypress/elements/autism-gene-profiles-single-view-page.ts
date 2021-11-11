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

        autism_scores[id].name = element.text();
        cy.wrap(table).get('td.ng-star-inserted').eq(id).then(scores => {
          cy.wrap(scores).get('g > text.small').then(value => {
            autism_scores[id].value = parseFloat(value.text());
          });
        });
      });
    });
    
    cy.wrap(autism_scores).as('autism_results');
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
        protection_scores[id].name = element.text();
        
        cy.wrap(table).get('td.ng-star-inserted').eq(id).then(scores => {
          cy.wrap(scores).get('g > text.small').then(value => {
            protection_scores[id].value = parseFloat(value.eq(id).text());
          });
        });
      });
    });
    
    cy.wrap(protection_scores).as('protection_results');
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

    cy.wrap(autism_gene_sets).as('autism_gene_results');
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

    cy.wrap(relevant_gene_sets).as('relevant_gene_results');
    return relevant_gene_sets;
  }

  getStudyTable(view: AutismGeneProfilesSingleView, tableId: number): any {
    let  study = [];

    view.datasetsTable.eq(tableId).then(table => {
      cy.wrap(table).get('.datasets-table > tbody > tr.ng-star-inserted').each((elv, num) => {
        cy.wrap(elv).within(el => {
          if(study[num] === undefined) {
            study[num] = {
              variant_statistics: '',
              variant_ids: '',
              affected: '',
              unaffected: '',
            }
          }
        
          cy.wrap(el).invoke('attr', 'id').then(id => {
            this.datasetsTableColumn(id, 0).then(name => {
              study[num].variant_statistics = name.text();
            });
            this.datasetsTableColumn(id, 1).then(affected => {
              study[num].affected = affected.text();
            });
            this.datasetsTableColumn(id, 2).then(unaffected => {
              study[num].unaffected = unaffected.text();
            });
            study[num].variant_ids = id;
          });
        });
      });  
    });
    
    cy.wrap(study).as('study_results');
    return study;
  }

  compareData(view: AutismGeneProfilesSingleView): any {
    let gene_data = {
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

    view.geneSymbol.then(symbol => {
      gene_data.gene_symbols = symbol.text();
    });

    gene_data.autism_scores = view.getAutismScores(view);
    gene_data.protection_scores = view.getProtectionScores(view);
    gene_data.statistics.autism_gene_sets = view.getAutismGeneSets(view);
    gene_data.statistics.relevant_gene_sets = view.getRelevantGeneSets(view);
    gene_data.statistics.study = view.getStudyTable(view, 0);

    cy.wrap(gene_data).as('result');
    return gene_data;
  }
}
