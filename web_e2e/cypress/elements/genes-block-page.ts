import { BasePage } from './utils';

export class GenesBlockPage extends BasePage {
  get window() {
    return cy.get('gpf-genes-block');
  }

  get allButton() {
    return cy.get('gpf-genes-block a').contains('All');
  }

  get geneSymbolsButton() {
    return cy.get('#gene-symbols');
  }

  get geneSymbolsPanel() {
    return cy.get('#gene-symbols-panel');
  }

  get geneSymbolsTextarea() {
    return cy.get('gpf-gene-symbols textarea');
  }

  get geneSetsButton() {
    return cy.get('#gene-sets');
  }

  get geneSetsPanel() {
    return cy.get('#gene-sets-panel');
  }

  get geneSetsSearchbox() {
    return cy.get('#search-box');
  }

  findGeneSetsSearchboxDropdownOptionsByText(text: string) {
    return cy.get('button.dropdown-item span').contains(text);
  }

  getFirstGeneSetFromDropdownMenu() {
    return cy.get('button.dropdown-item span').first();
  }

  get geneSetsFromDropdownMenu() {
    return cy.get('button.dropdown-item span');
  }

  // async presenceOfOneElement(elementArrayFinder: ElementArrayFinder) {
  //   return function () {
  //       return elementArrayFinder.count().then(function (currentCount) {
  //           return currentCount === 1;
  //       });
  //   };
  // }

  get selectedGeneSet() {
    return cy.get('#selected-value');
  }

  get geneSetCountElement() {
    return cy.get('gpf-gene-sets > div > div div.ng-star-inserted').contains('Count');
  }

  get downloadButton() {
    return cy.get('gpf-gene-sets a').contains('Download');
  }

  get geneSetsCollectionSelectorDropdownMenu() {
    return cy.get('gpf-gene-sets select.form-control');
  }

  findGeneSetsCollectionOptionByText(text: string) {
    return cy.get('gpf-gene-sets option').contains(text);
  }

  findDenovoDropdownByText(text: string) {
    return cy.get('ngb-accordion span').contains(text);
  }

  get geneWeightsButton() {
    return cy.get('#gene-weights');
  }

  get genesWeightsPanel() {
    return cy.get('#gene-weights-panel');
  }

  findDenovoGeneSetCollectionCheckbox(genotypeDataId: string, peopleGroupValue: string) {
    const checkboxId: string = genotypeDataId + '-checkbox-' + peopleGroupValue;
    return cy.get(`#${checkboxId}`);
  }
}
