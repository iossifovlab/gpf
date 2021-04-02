import { BasePage } from './utils';

export class GeneViewPage extends BasePage {
  get window() {
    return cy.get('gpf-gene-view');
  }

  get affectedStatusAffectedOnlyCheckbox() {
    return cy.get('input[id="affectedStatusAffected only-checkbox"]');
  }

  get affectedStatusUnaffectedOnlyCheckbox() {
    return cy.get('input[id="affectedStatusUnaffected only-checkbox"]');
  }

  get affectedStatusAffectedAndUnaffectedCheckbox() {
    return cy.get('input[id="affectedStatusAffected and unaffected-checkbox"]');
  }

  get effectTypesLGDsCheckbox() {
    return cy.get('label').contains('LGDs').first().get('input');
  }

  get effectTypesMissenseCheckbox() {
    return cy.get('label').contains('Missense').first().get('input');
  }

  get effectTypesSynonymousCheckbox() {
    return cy.get('label').contains('Synonymous').first().get('input');
  }

  get effectTypesCNVPlusCheckbox() {
    return cy.get('label').contains('CNV+').first().get('input');
  }

  get effectTypesCNVMinusCheckbox() {
    return cy.get('label').contains('CNV-').first().get('input');
  }

  get effectTypesOtherCheckbox() {
    return cy.get('label').contains('Other').first().get('input');
  }

  get inheritanceTypesDenovoCheckbox() {
    return cy.get('label').contains('Denovo').first().get('input');
  }

  get inheritanceTypesTransmittedCheckbox() {
    return cy.get('label').contains('Transmitted').first().get('input');
  }

  get variantTypesSubCheckbox() {
    return cy.get('label').contains('sub').first().get('input');
  }

  get variantTypesInsCheckbox() {
    return cy.get('label').contains('ins').first().get('input');
  }

  get variantTypesDelCheckbox() {
    return cy.get('label').contains('del').first().get('input');
  }

  get variantTypesCNVPlusCheckbox() {
    return cy.get('label').contains('CNV+').eq(0).get('input');
  }

  get variantTypesCNVMinusCheckbox() {
    return cy.get('label').contains('CNV-').eq(0).get('input');
  }

  get undoButton() {
    return cy.get('button[title="Undo (Ctrl+Z)"]');
  }

  get redoButton() {
    return cy.get('button[title="Redo (Ctrl+Y)"]');
  }

  get resetButton() {
    return cy.get('button[title="Reset (Double-click)"]');
  }

  get hideTranscriptsCheckbox() {
    return cy.get('label').contains('Hide transcripts').first().get('input');
  }

  get condenseIntronsCheckbox() {
    return cy.get('label').contains('Condense introns').first().get('input');
  }

  get downloadButton() {
    return cy.get('button').contains(/^Download$/);
  }

  get downloadSummaryButton() {
    return cy.get('button').contains('Download Summary');
  }
}
