import { BasePage } from './utils';

export class FamilyFilterBlockPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-family-filters-block');
  }

  public get allButton(): element {
    return cy.get('#all-families');
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

  public get histogram(): element {
    return cy.get('div.histogram > svg');
  }

  public get searchbox(): element {
    return cy.get('gpf-family-filters-block input#tags');
  }

  public get dropdownMenu(): element {
    return cy.get('.ui-front');
  }

  public getDropdownMenuOptionByText(text: string): element {
    return cy.get('.ui-menu-item-wrapper').contains(text);
  }

  public get fromInputField(): element {
    return cy.get('#from-input-field');
  }

  public get toInputField(): element {
    return cy.get('#to-input-field');
  }
}
