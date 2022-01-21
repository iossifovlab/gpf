import { BasePage } from './utils';

export class EnrichmentModelsBockPage extends BasePage {
  get window() {
    return cy.get('gpf-enrichment-models-block');
  }

  get selectModelsButton() {
    return cy.get('#select-models');
  }

  get backgroundModelsDropdown() {
    return cy.get('#background-models select');
  }

  get countingModelsDropdown() {
    return cy.get('#counting-models select');
  }
}
