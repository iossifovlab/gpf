import { BasePage } from "./utils";

export class RegionsBlockPage extends BasePage {
  get block() {
    return cy.get('gpf-regions-block');
  }

  get regionsFilterButton() {
    return cy.get('#regions-filter');
  }

  get regionsFilterPanel() {
    return cy.get('#regions-filter-panel');
  }

  get regionsFilterTextarea() {
    return cy.get('gpf-regions-filter textarea');
  }
}
