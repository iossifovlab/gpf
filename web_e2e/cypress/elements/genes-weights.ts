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
}