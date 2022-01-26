import { BasePage } from './utils';

export class ShareQueryPage extends BasePage {
  public get button(): element {
    return cy.get('#share-query-dropdown-button');
  }

  public get dropdownMenu(): element {
    return cy.get('#share-query-dropdown');
  }

  public get input(): element {
    return cy.get('div#share-query-dropdown input');
  }
}
