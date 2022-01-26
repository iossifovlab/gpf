import { BasePage } from './utils';

export class PhenoToolPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-pheno-tool');
  }

  public get genotypeBlockPanel(): element {
    return cy.get('gpf-pheno-tool-genotype-block');
  }

  public get resultsChart(): element {
    return cy.get('gpf-pheno-tool-results-chart');
  }

  public get reportButton(): element {
    return cy.get('gpf-pheno-tool button').contains('Report');
  }
}
