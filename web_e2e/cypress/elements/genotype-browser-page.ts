import { BasePage } from './utils';

export class GenotypeBrowserPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-genotype-browser');
  }

  public get tablePreviewButton(): element {
    return cy.get('#table-preview-button');
  }

  public get downloadButton(): element {
    return cy.get('#download-button');
  }

  public get overviewParagraph(): element {
    return cy.get('#variants-count-span');
  }

  public get loadingScreenElement(): element {
    return cy.get('.overlay');
  }

  public get alertElement(): element {
    return cy.get('div.alert.alert-danger.ng-star-inserted');
  }
}