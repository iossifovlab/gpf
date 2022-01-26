import { BasePage } from './utils';

export class GeneBrowserPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-gene-browser');
  }

  public get searchInputBox(): element {
    return cy.get('gpf-gene-browser input#search-box');
  }

  public get goButton(): element {
    return cy.get('input[value=\'Go\']');
  }

  public get genotypePreviewTable(): element {
    return cy.get('gpf-genotype-preview-table');
  }

  public get codingOnlyCheckbox(): element {
    return cy.get('input#coding-only-checkbox');
  }

  public get affectedStatusField(): element {
    return cy.get('div#affected-status-filters');
  }

  public get effectTypeFiltersField(): element {
    return cy.get('div#effect-types-filters');
  }

  public get inheritanceTypesFilter(): element {
    return cy.get('div#inheritance-types-filters');
  }

  public get variantTypesFilter(): element {
    return cy.get('div#variant-types-filters');
  }

  public getAffectedStatusCheckbox(affectedStatus: string): element {
    return cy.get('.filter-label span').contains(affectedStatus);
  }

  public getEffectTypesCheckbox(effectType: string): element {
    return cy.get('#effect-types-filters span').contains(effectType);
  }

  public getInheritanceTypes(inheritanceType: string): element {
    return cy.get('#inheritance-types-filters span').contains(inheritanceType);
  }

  public getVariantTypes(variantType: string): element {
    return cy.get('#variant-types-filters span').contains(variantType);
  }

  public get legend(): element {
    return cy.get('.legend-div');
  }
}
