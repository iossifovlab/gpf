import { BasePage } from './utils';

export class GeneViewPage extends BasePage {
  get window() {
    return cy.get('gpf-gene-view');
  }

  getAffectedStatusCheckbox(affectedStatus: string) {
    return cy.get('label').contains(affectedStatus).siblings('input');
  }

  getEffectTypesCheckbox(effectType: string) {
    effectType = effectType.replace('+', '\\+');
    return cy.get(`svg#${effectType}`).siblings('input');
  }

  getInheritanceTypes(inheritanceType: string) {
    inheritanceType = inheritanceType.toLowerCase();
    return cy.get(`svg#${inheritanceType}`).siblings('input');
  }

  getVariantTypes(variantType: string) {
    return cy.get('div.card-header').contains('Variant Types')
    .siblings('div').find('label').contains(variantType).find('input').first();
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
