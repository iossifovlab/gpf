import { BasePage } from './utils';

export class GenomicScoresBlockPage extends BasePage {
  get block() {
    return cy.get('gpf-genomic-scores-block');
  }

  get panel() {
    return cy.get('gpf-genomic-scores');
  }

  get histogram() {
    return cy.get('gpf-histogram');
  }

  get fromInputField() {
    return cy.get('input#from-input-field');
  }

  get toInputField() {
    return cy.get('input#to-input-field');
  }

  get filterSelect() {
    return cy.get('select.form-control');
  }

  get histogramRangeSelectors() {
    return cy.get('text.partitions-text');
  }

  get addFilterButton() {
    return cy.get('gpf-genomic-scores-block gpf-add-button');
  }

  get removeFilterButton() {
    return cy.get('gpf-remove-button > img.clickable');
  }
}
