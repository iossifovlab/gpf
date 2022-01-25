import { BasePage } from './utils';

export class GeneWeightsPage extends BasePage {
  get dropdownButton() {
    return cy.get('gpf-gene-weights select');
  }

  get fromInputField() {
    return cy.get('input#from-input-field');
  }

  get toInputField() {
    return cy.get('input#to-input-field');
  }

  get fromFieldStepUp() {
    return cy.get('.histogram-from .step.up');
  }

  get fromFieldStepDown() {
    return cy.get('.histogram-from .step.down');
  }

  get toFieldStepUp() {
    return cy.get('.histogram-to .step.up');
  }

  get toFieldStepDown() {
    return cy.get('.histogram-to .step.down');
  }

  get allGeneWeights() {
    return cy.get('text#sumOfBarsLabel');
  }
  
  get histogram() {
    return cy.get('div.histogram > svg');
  }
}
