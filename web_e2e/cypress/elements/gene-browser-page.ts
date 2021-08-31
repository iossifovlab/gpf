import { BasePage } from './utils';

export class GeneBrowserPage extends BasePage {
  get window() {
    return cy.get('gpf-gene-browser');
  }

  get searchInputBox() {
    return cy.get('gpf-gene-browser input#search-box');
  }

  get goButton() {
    return cy.get('input[value=\'Go\']');
  }

  get genePlot() {
    return cy.get('gpf-gene-plot');
  }

  get genotypePreviewTable() {
    return cy.get('gpf-genotype-preview-table');
  }

  get codingOnlyCheckbox() {
    return cy.get('input#coding-only-checkbox');
  }
}
