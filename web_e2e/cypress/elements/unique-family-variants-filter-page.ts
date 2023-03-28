import { BasePage } from './utils';

export class UniqueFamilyVariantsFilterPage extends BasePage {
  public get block(): element {
    return cy.get('#unique-family-variants-block');
  }

  public get UniqueFamilyVariantsCheckbox(): element {
    return cy.get('#unique-family-variants-checkbox');
  }
}
