import { BasePage } from './utils';

export class DatasetsPage extends BasePage {
  public get datasetStatisticsWindow(): element {
    return cy.get('gpf-variant-reports');
  }

  public get permissionDeniedPrompt(): element {
    return cy.get('#permission-denied-prompt');
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

  public get familiesByNumberDropdownButton(): element {
    return cy.get('#families-by-number-dropdown-button');
  }

  public get allFamiliesByNumberHeaderCells(): element {
    return cy.get('div#families-by-number-div tbody th');
  }

  public get allFamiliesByNumberDataCells(): element {
    return cy.get('div#families-by-number-div td');
  }

  public get familiesByPedigreeDivs(): element {
    return cy.get('gpf-common-reports-pedigree-cell div.pedigree-count');
  }

  public findDenovoVariantsCountsByRowName(rowName: string): element {
    return cy.get('div#denovo-variants-div th').contains(rowName).parent().find('div');
  }

  public get denovoVariantsDropdownButton(): element {
    return cy.get('#denovo-variants-dropdown-button');
  }
}
