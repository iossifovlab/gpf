import { BasePage } from './utils';

export class FamilyFilterBlockPage extends BasePage {
  get window() {
    return cy.get('gpf-family-filters-block');
  }

  get allButton() {
    return cy.get('#all-families');
  }

  get tabPanel() {
    return cy.get('.tab-pane active');
  }

  get familyIdsButton() {
    return cy.get('#family-ids');
  }

  get familyIdsPanel() {
    return cy.get('#family-ids-panel');
  }

  get advancedButton() {
    return cy.get('gpf-family-filters-block a').contains('Advanced');
  }

  get phenoFiltersPanel() {
    return cy.get('#pheno-filters-panel');
  }

  get familyIdsTextarea() {
    return cy.get('gpf-family-ids textarea');
  }
}
