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

  get geneRelevantGeneSetsTable() {
    return cy.get('#relevant_gene_sets');
  }

  get datasetsTable() {
    return cy.get('.datasets-table');
  }

  get externalLinksTable() {
    return cy.get('#external-links');
  }
}
