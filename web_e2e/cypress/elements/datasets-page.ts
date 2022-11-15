import { BasePage } from './utils';

export class DatasetsPage extends BasePage {
  public get datasetStatisticsWindow(): element {
    return cy.get('gpf-variant-reports');
  }

  public get permissionDeniedPrompt(): element {
    return cy.get('#permission-denied-prompt');
  }

  public get datasetDescriptionButton(): element {
    cy.get('.navbar-custom').should('be.visible');
    return cy.get('a.nav-link').contains('Dataset Description');
  }

  public get datasetStatisticsButton(): element {
    cy.get('.navbar-custom').should('be.visible');
    return cy.get('a.nav-link').contains('Dataset Statistics');
  }

  public get genotypeBrowserButton(): element {
    cy.get('.navbar-custom').should('be.visible');
    return cy.get('a.nav-link').contains('Genotype Browser');
  }

  public get phenotypeBrowserButton(): element {
    cy.get('.navbar-custom').should('be.visible');
    return cy.get('a.nav-link').contains('Phenotype Browser');
  }

  public get phenotypeToolButton(): element {
    cy.get('.navbar-custom').should('be.visible');
    return cy.get('a.nav-link').contains('Phenotype Tool');
  }

  public get geneBrowserButton(): element {
    cy.get('.navbar-custom').should('be.visible');
    return cy.get('a.nav-link').contains('Gene Browser');
  }
}
