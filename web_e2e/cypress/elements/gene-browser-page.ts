import { BasePage } from './utils';

export class GeneBrowserPage extends BasePage {
  public get window(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('gpf-gene-browser');
  }

  public get searchInputBox(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('gpf-gene-browser input#search-box');
  }

  public get goButton(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('input[value=\'Go\']');
  }

  public get genotypePreviewTable(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('gpf-genotype-preview-table');
  }

  public get codingOnlyCheckbox(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('input#coding-only-checkbox');
  }

  public get affectedStatusField(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('div#affected-status-filters');
  }

  public get effectTypeFiltersField(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('div#effect-types-filters');
  }

  public get inheritanceTypesFilter(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('div#inheritance-types-filters');
  }

  public get variantTypesFilter(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('div#variant-types-filters');
  }

  public getAffectedStatusCheckbox(affectedStatus: string): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('.filter-label span').contains(affectedStatus);
  }

  public getEffectTypesCheckbox(effectType: string): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('#effect-types-filters span').contains(effectType);
  }

  public getInheritanceTypes(inheritanceType: string): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('#inheritance-types-filters span').contains(inheritanceType);
  }

  public getVariantTypes(variantType: string): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('#variant-types-filters span').contains(variantType);
  }

  public get legend(): Cypress.Chainable<JQuery<HTMLElement>> {
    return cy.get('.legend-div');
  }
}
