import { BasePage } from './utils';

export class GenomicScoresBlockPage extends BasePage {
  get block() {
    return cy.get('gpf-genomic-scores-block');
  }

  get panel() {
    return cy.get('gpf-genomic-scores');
  }

  get addFilterButton() {
    return cy.get('gpf-genomic-scores-block gpf-add-button');
  }

  get removeFilterButton() {
    return cy.get('gpf-remove-button > img.clickable');
  }
}
