import { BasePage } from './utils';

export class PersonFiltersBlockPage extends BasePage {
  public get block(): element {
    return cy.get('gpf-person-filters-block');
  }
}
