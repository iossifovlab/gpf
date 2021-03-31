import { BasePage } from './utils';

export class PhenoToolPage extends BasePage {
  get window() {
    return cy.get('gpf-pheno-tool');
  }

  get genotypeBlockPanel() {
    return cy.get('gpf-pheno-tool-genotype-block');
  }

  get resultsChart() {
    return cy.get('gpf-pheno-tool-results-chart');
  }

  get reportButton() {
    return cy.get('gpf-pheno-tool button').contains('Report');
  }
}
