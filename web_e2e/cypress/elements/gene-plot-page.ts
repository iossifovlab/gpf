import { BasePage } from './utils';

export class GenePlotPage extends BasePage {
  get window() {
    return cy.get('gpf-plot-view');
  }

  getAffectedStatusCheckbox(affectedStatus: string) {
    return cy.get('.filter-label span').contains(affectedStatus);
  }

  getEffectTypesCheckbox(effectType: string) {
    return cy.get('#effect-types-filters span').contains(effectType);
  }

  getInheritanceTypes(inheritanceType: string) {
    return cy.get('#inheritance-types-filters span').contains(inheritanceType);
  }

  getVariantTypes(variantType: string) {
    return cy.get('#variant-types-filters span').contains(variantType);
  }

  get undoButton() {
    return cy.get('#undo-button');
  }

  get redoButton() {
    return cy.get('#redo-button');
  }

  get resetButton() {
    return cy.get('#reset-button');
  }

  get hideTranscriptsCheckbox() {
    return cy.get('label').contains('Hide transcripts').first();
  }

  get condenseIntronsCheckbox() {
    return cy.get('.checkbox-option').contains('Condense introns').first();
  }

  get downloadButton() {
    return cy.get('button').contains(/^Download$/);
  }

  get downloadSummaryButton() {
    return cy.get('button').contains('Download Summary');
  }

  get variantsCount() {
    return cy.get('span#summary-alleles-count span');
  }

  get affectedStatusField() {
    return cy.get('div#affected-status-filters');
  }

  get effectTypeFiltersField() {
    return cy.get('div#effect-types-filters');
  }

  get inheritanceTypesFilter() {
    return cy.get('div#inheritance-types-filters');
  }

  get variantTypesFilter() {
    return cy.get('div#variant-types-filters');
  }

  get legend() {
    return cy.get('.legend-div > div > div > span');
  }
}
