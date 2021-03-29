import { BasePage } from "./utils";

export class GenotypeBrowserPage extends BasePage {
  get window() {
    return cy.get('gpf-genotype-browser');
  }

  get tablePreviewButton() {
    return cy.get('#table-preview-button');
  }

  get downloadButton() {
    return cy.get('#download-button');
  }

  get overviewParagraph() {
    return cy.get('#variants-count-span');
  }

  get loadingScreenElement() {
    return cy.get('.overlay');
  }

  get alertElement() {
    return cy.get('div.alert.alert-danger.ng-star-inserted');
  }
}