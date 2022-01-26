import { BasePage } from './utils';

export class PhenoToolMeasurePage extends BasePage {
  public get block(): element {
    return cy.get('gpf-pheno-tool-measure');
  }

  public get searchbox(): element {
    return cy.get('gpf-pheno-tool-measure input#search-box');
  }

  public get searchboxAlert(): element {
    return cy.get('li').contains('measure should not be empty');
  }
}
