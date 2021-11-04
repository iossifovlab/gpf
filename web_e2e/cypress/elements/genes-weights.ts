import { BasePage } from './utils';

export class GenesWeights extends BasePage {
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

  dragLine(which: string) {
    switch(which) {
      case 'left': {
        return cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(0);
      }
      case 'right': {
        return cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(1)
      }
      default: {
        return cy.get('g[gpf-histogram-range-selector-line] > g > line');
      }
    }
  }

  moveSlider(which: string, percentage: number) {
    switch(which) {
      case 'left': {
        dragTo(this.dragLine('left'), this.dragLine('right'));
        //dragTo(this.dragLine(''));
        break;        
      }
      case 'right': {
        /*let obj = cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(1);
        obj.trigger('dragstart');
        cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(1)
        .trigger('drop');*/
        //dragTo(this.dragLine('left'), this.dragLine('right'));
        break;    
      }
      default: {
        return;
      }
    }
  }
}

function dragTo (subject, targetEl) {
  subject.trigger("mousedown", {which: 1});
  targetEl.trigger("mousemove");
  targetEl.trigger("mouseup", {force: true});
}
