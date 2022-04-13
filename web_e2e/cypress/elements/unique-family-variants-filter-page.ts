import { BasePage } from './utils';

export class UniqueFamilyVariantsFilterPage extends BasePage {
  public get block(): element {
    return cy.get('#unique-family-variants-block');
  }
}
