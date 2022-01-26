import { BasePage } from './utils';

export class GenomicScoresBlockPage extends BasePage {
  public get block(): element {
    return cy.get('gpf-genomic-scores-block');
  }

  public get panel(): element {
    return cy.get('gpf-genomic-scores');
  }

  public get histogram(): element {
    return cy.get('gpf-histogram');
  }

  public get fromInputField(): element {
    return cy.get('input#from-input-field');
  }

  public get toInputField(): element {
    return cy.get('input#to-input-field');
  }

  public get filterSelect(): element {
    return cy.get('select.form-control');
  }

  public get histogramRangeSelectors(): element {
    return cy.get('text.partitions-text');
  }

  public get addFilterButton(): element {
    return cy.get('gpf-genomic-scores-block gpf-add-button');
  }

  public get removeFilterButton(): element {
    return cy.get('gpf-remove-button > img.clickable');
  }
}
