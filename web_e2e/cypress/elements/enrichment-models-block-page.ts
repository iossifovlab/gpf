import { BasePage } from './utils';

export class EnrichmentModelsBockPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-enrichment-models-block');
  }

  public get selectModelsButton(): element {
    return cy.get('#select-models');
  }

  public get backgroundModelsDropdown(): element {
    return cy.get('#background-models select');
  }

  public get countingModelsDropdown(): element {
    return cy.get('#counting-models select');
  }
}
