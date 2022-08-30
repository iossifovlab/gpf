import { BasePage } from './utils';

export class SaveQueryPage extends BasePage {
  public get button(): element {
    return cy.get('#save-query-dropdown-button');
  }

  public get dropdownMenu(): element {
    return cy.get('#save-query-dropdown');
  }

  public get copyLinkButton(): element {
    return cy.get('#copy-link-button');
  }

  public get copiedTooltip(): element {
    return cy.get('ngb-tooltip-window');
  }

  public get linkInput(): element {
    return cy.get('#link-input');
  }

  public get nameInput(): element {
    return cy.get('gpf-save-query #name');
  }

  public get descriptionInput(): element {
    return cy.get('gpf-save-query #description')
  }

  public get saveButton(): element {
    return cy.get('gpf-save-query #save-button');
  }
}
