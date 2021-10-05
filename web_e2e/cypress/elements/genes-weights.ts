import { GenesBlockPage } from './genes-block-page';
import { BasePage } from './utils';

export class GenesWeights extends GenesBlockPage {
  get buttonsLowRange() {
    return cy.get('div.histogram-from > div.stepper > button');
  }

  get buttonsHighRange() {
    return cy.get('div.histogram-to > div.stepper > button');
  }

  get fieldLowRange() {
    return cy.get('div.histogram-from > div.stepper > input');
  }

  get fieldHighRange() {
    return cy.get('div.histogram-to > div.stepper > input');
  }

  get selectField() {
    return cy.get('gpf-gene-weights select');
  }

  get sumOfBars() {
    return cy.get('text#sumOfBarsLabel');
  }

  get graphicsTextArray() {
    return cy.get('g > text');
  }

  get inputFiledMin() {
    return cy.get('input#from-input-field');
  }

  get inputFiledMax() {
    return cy.get('input#to-input-field');
  }

  get gpfErrorAlert() {
    return cy.get('div.alert');
  }

  get effectPanel() {
    return cy.get('.col-lg-6');
  }

  get tablePreview() {
    return cy.get('input#table-preview-button');
  }
}
