import { BasePage } from './utils';


export class PhenoToolMeasurePage extends BasePage {
  get block() {
    return cy.get('gpf-pheno-tool-measure');
  }

  get searchbox() {
    return cy.get('gpf-pheno-tool-measure input#search-box');
  }

  get searchboxAlert() {
    return cy.get('li').contains('measure should not be empty');
  }
}
