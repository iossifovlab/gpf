import { BasePage } from './utils';

export class GeneBrowserPage extends BasePage {
  get window() {
    return cy.get('gpf-gene-browser');
  }

  get searchInputBox() {
    return cy.get('gpf-gene-browser input#search-box');
  }

  get goButton() {
    return cy.get('input[value=\'Go\']');
  }

  get genotypePreviewTable() {
    return cy.get('gpf-genotype-preview-table');
  }

  get codingOnlyCheckbox() {
    return cy.get('input#coding-only-checkbox');
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

  get legend() {
    return cy.get('.legend-div');
  }
}
