import { BasePage } from './utils';

export class GenePlotPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-gene-plot');
  }

  public get undoButton(): element {
    return cy.get('#undo-button');
  }

  public get redoButton(): element {
    return cy.get('#redo-button');
  }

  public get resetButton(): element {
    return cy.get('#reset-button');
  }

  public get variantsCount(): element {
    return cy.get('#variants-count-span');
  }

  public get hideTranscriptsCheckbox(): element {
    return cy.get('label').contains('Hide transcripts').first();
  }

  public get condenseIntronsCheckbox(): element {
    return cy.get('.checkbox-option').contains('Condense introns').first();
  }

  public get geneTitle(): element {
    return cy.get('#gene-title');
  }

  public get summaryAllelesCount(): element {
    return cy.get('#summary-alleles-count span');
  }

  public get familyVariantsCount(): element {
    return cy.get('#family-variants-count span');
  }

  public get downloadSummaryButton(): element {
    return cy.get('button').contains('Download Summary');
  }

  public get downloadButton(): element {
    return cy.get('button').contains(/^Download$/);
  }
}
