import { BasePage } from './utils';

export class GeneWeightsPage extends BasePage {
  public get dropdownButton(): element {
    return cy.get('gpf-gene-weights select');
  }

  public get fromInputField(): element {
    return cy.get('input#from-input-field');
  }

  public get toInputField(): element {
    return cy.get('input#to-input-field');
  }

  public get fromFieldStepUp(): element {
    return cy.get('.histogram-from .step.up');
  }

  public get fromFieldStepDown(): element {
    return cy.get('.histogram-from .step.down');
  }

  public get toFieldStepUp(): element {
    return cy.get('.histogram-to .step.up');
  }

  public get toFieldStepDown(): element {
    return cy.get('.histogram-to .step.down');
  }

  public get allGeneWeights(): element {
    return cy.get('text#sumOfBarsLabel');
  }

  public get histogram(): element {
    return cy.get('div.histogram > svg');
  }
}
