import { BasePage } from './utils';

export class FamilyFilterBlockPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-family-filters-block');
  }

  public get allButton(): element {
    return cy.get('#all-families');
  }

  public get tabPanel(): element {
    return cy.get('.tab-pane active');
  }

  public get familyIdsButton(): element {
    return cy.get('#family-ids');
  }

  public get familyIdsPanel(): element {
    return cy.get('#family-ids-panel');
  }

  public get advancedButton(): element {
    return cy.get('gpf-family-filters-block a').contains('Advanced');
  }

  public get phenoFiltersPanel(): element {
    return cy.get('#pheno-filters-panel');
  }

  public get familyIdsTextarea(): element {
    return cy.get('gpf-family-ids textarea');
  }
}
