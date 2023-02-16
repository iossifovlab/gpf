import { BasePage, longTimeout } from './utils';

export class PhenoToolPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-pheno-tool');
  }

  public get genotypeBlockPanel(): element {
    return cy.get('gpf-pheno-tool-genotype-block');
  }

  public get presentInParent(): element {
    return cy.get('gpf-present-in-parent');
  }

  public get effectTypes(): element {
    return cy.get('gpf-pheno-tool-effect-types');
  }

  public get resultsChart(): element {
    return cy.get('gpf-pheno-tool-results-chart');
  }

  public get reportButton(): element {
    return cy.get('gpf-pheno-tool button').contains('Report');
  }

  public get downloadButton(): element {
    return cy.get('gpf-pheno-tool button').contains('Download');
  }

  public pressReportButton(): void {
    this.reportButton.click();
    cy.get('gpf-pheno-tool-results-chart', {timeout: longTimeout}).should('be.visible');
  }
}
