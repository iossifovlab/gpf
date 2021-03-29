import { BasePage } from './utils';

export class AutismGeneProfilesSingleView extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profile-single-view');
  }

  get header() {
    return cy.get('gpf-autism-gene-profile-single-view h2');
  }

  get headerGeneName() {
    return this.header.invoke('text');
  }

  get geneBrowserLink() {
    return cy.get('gpf-autism-gene-profile-single-view a');
  }

  get autismScoresTable() {
    return cy.get('#autism-scores-table');
  }

  get protectionScoresTable() {
    return cy.get('#protection-scores-table');
  }

  get geneSetsTable() {
    return cy.get('#gene-sets-table');
  }
}
