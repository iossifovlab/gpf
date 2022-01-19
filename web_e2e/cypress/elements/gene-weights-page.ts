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

  moveSlider(which: string, dragValue, heightValue: number = 0) {
    if (which === 'right') {
      dragValue = -dragValue;
    }

    cy.window().then((win) => {
      cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(which === 'left' ? 0 : 1)
        .trigger("mousedown", 0, heightValue, { // start value, height value
            view: win,
            which: 1,
            force: true,
            bubbles: true
        })
        .trigger("mousemove", dragValue, heightValue, { // how much to be dragged value, height value
            which: 1,
            force: true,
            bubbles: true
        })
        .trigger("mouseup", 0, heightValue, { // end value, height value
            which: 1,
            force: true,
            view: win,
            bubbles: true
        });
    });     
  }

  getTextPartitionValue(which: string): void {
    this.partitionsText(which).then(values => {
      cy.wrap(values.text()).as('weightsPartitionValue');
    });
  }

  partitionsText(which: string) {
    return cy.get('text.partitions-text.ng-star-inserted').eq(which === 'left' ? 0 : 1);
  }

  getInput(which: string) {
    return cy.get('input#' + (which === 'left' ? 'from-input-field' : (which === 'right' ? 'to-input-field' : null)));
  }

  setInputFieldValue(which: string, value: string) {
    this.getInput(which).then(input => {
      cy.wrap(input).clear().type(value);
    });
  }

  clickInputField(which: string, where: string, times: number) {
    cy.get('div.stepper').eq(which === 'left' ? 0 : (which === 'right' ? 1 : null)).within(input => {
      cy.wrap(input).get(where === 'up' ? 'button.step.up' : (where === 'down' ? 'button.step.down' : null)).then(button => {
        while(times !== 0) {
          cy.wrap(button).click();
          times--;
        }
      });
    });
  }
}
