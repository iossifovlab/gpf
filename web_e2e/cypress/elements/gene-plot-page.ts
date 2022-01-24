import { BasePage } from './utils';

export class GenePlotPage extends BasePage {
  get window() {
    return cy.get('gpf-gene-plot');
  }

  get undoButton() {
    return cy.get('#undo-button');
  }

  get redoButton() {
    return cy.get('#redo-button');
  }

  get resetButton() {
    return cy.get('#reset-button');
  }

  get variantsCount() {
    return cy.get('#variants-count-span');
  }

  get hideTranscriptsCheckbox() {
    return cy.get('label').contains('Hide transcripts').first();
  }

  get condenseIntronsCheckbox() {
    return cy.get('.checkbox-option').contains('Condense introns').first();
  }

  get geneTitle() {
    return cy.get('#gene-title');
  }

  get summaryAllelesCount() {
    return cy.get('#summary-alleles-count span');
  }

  get familyVariantsCount() {
    return cy.get('#family-variants-count span');
  }

  get downloadSummaryButton() {
    return cy.get('button').contains('Download Summary');
  }

  get downloadButton() {
    return cy.get('button').contains(/^Download$/);
  }
}
