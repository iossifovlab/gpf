import { BasePage } from './utils';

export class AutismGeneProfilesSingleView extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profile-single-view');
  }

  get header() {
    return cy.get('gpf-autism-gene-profile-single-view h2');
  }

  get geneBrowserLink() {
    return cy.get('gpf-autism-gene-profile-single-view a');
  }

  get autismScoresTable() {
    return cy.get('#autism_scores');
  }

  get protectionScoresTable() {
    return cy.get('#protection_scores');
  }

  get geneAutismGeneSetsTable() {
    return cy.get('#autism_gene_sets');
  }

  get geneRelevantGeneSetsTable() {
    return cy.get('#relevant_gene_sets');
  }
}
