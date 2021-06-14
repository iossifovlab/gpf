import { BasePage } from './utils';

export class DatasetsPage extends BasePage {
  get datasetStatisticsWindow() {
    return cy.get('gpf-variant-reports');
  }

  get permissionDeniedPrompt() {
    return cy.get('#permission-denied-prompt');
  }

  get datasetsDropdownMenuButton() {
    return cy.get('#datasets-dropdown-menu-button');
  }

  get datasetsDropdownMenuElements() {
    return cy.get('.dataset-selector a');
  }

  get datasetStatisticsButton() {
    return cy.get('a.nav-link').contains('Dataset Statistics');
  }

  get genotypeBrowserButton() {
    return cy.get('a.nav-link').contains('Genotype Browser');
  }

  get phenotypeBrowserButton() {
    return cy.get('a.nav-link').contains('Phenotype Browser');
  }

  get phenotypeToolButton() {
    return cy.get('a.nav-link').contains('Phenotype Tool');
  }

  get geneBrowserButton() {
    return cy.get('a.nav-link').contains('Gene Browser');
  }

  get familiesByNumberDropdownButton() {
    return cy.get('#families-by-number-dropdown-button');
  }

  getFamiliesByNumberDropdownOptionByText(text: string) {
    return cy.get('#families-by-number-dropdown-button option').contains(text);
  }

  get allFamiliesByNumberHeaderCells() {
    return cy.get('div#families-by-number-div tbody th');
  }

  get allFamiliesByNumberDataCells() {
    return cy.get('div#families-by-number-div td');
  }

  get familiesByPedigreeDivs() {
    return cy.get('gpf-common-reports-pedigree-cell > div > div');
  }

  getDenovoTableHeaderElements() {
    return cy.get('div#denovo-variants-div thead div');
  }

  findDenovoVariantsCountsByRowName(rowName: string) {
    return cy.get('div#denovo-variants-div th').contains(rowName).parent().find('div');
  }

  get denovoVariantsDropdownButton() {
    return cy.get('#denovo-variants-dropdown-button');
  }

  getDenovoVariantsDropdownOptionByText(text: string) {
    return cy.get('#denovo-variants-dropdown-button option').contains(text);
  }
}
