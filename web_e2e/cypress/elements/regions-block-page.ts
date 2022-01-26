import { BasePage } from './utils';

export class RegionsBlockPage extends BasePage {
  public get block(): element {
    return cy.get('gpf-regions-block');
  }

  public get regionsFilterButton(): element {
    return cy.get('#regions-filter');
  }

  public get regionsFilterPanel(): element {
    return cy.get('#regions-filter-panel');
  }

  public get regionsFilterTextarea(): element {
    return cy.get('gpf-regions-filter textarea');
  }
}
