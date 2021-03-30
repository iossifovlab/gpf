import { BasePage } from "./utils";

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

  // get effectTypesMissenseCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Missense')).get(0).element(by.css('input'));
  // }

  // get effectTypesSynonymousCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Synonymous')).get(0).element(by.css('input'));
  // }

  // get effectTypesCNVPlusCheckbox() {
  //   return element.all(by.cssContainingText('label', 'CNV+')).get(0).element(by.css('input'));
  // }

  // get effectTypesCNVMinusCheckbox() {
  //   return element.all(by.cssContainingText('label', 'CNV-')).get(0).element(by.css('input'));
  // }

  // get effectTypesOtherCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Other')).get(0).element(by.css('input'));
  // }

  // get inheritanceTypesDenovoCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Denovo')).get(0).element(by.css('input'));
  // }

  // get inheritanceTypesTransmittedCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Transmitted')).get(0).element(by.css('input'));
  // }

  // get variantTypesSubCheckbox() {
  //   return element.all(by.cssContainingText('label', 'sub')).get(0).element(by.css('input'));
  // }

  // get variantTypesInsCheckbox() {
  //   return element.all(by.cssContainingText('label', 'ins')).get(0).element(by.css('input'));
  // }

  // get variantTypesDelCheckbox() {
  //   return element.all(by.cssContainingText('label', 'del')).get(0).element(by.css('input'));
  // }

  // get variantTypesCNVPlusCheckbox() {
  //   return element.all(by.cssContainingText('label', 'CNV+')).get(1).element(by.css('input'));
  // }

  // get variantTypesCNVMinusCheckbox() {
  //   return element.all(by.cssContainingText('label', 'CNV-')).get(1).element(by.css('input'));
  // }

  // get undoButton() {
  //   return element(by.css('button[title="Undo (Ctrl+Z)"]'));
  // }

  // get redoButton() {
  //   return element(by.css('button[title="Redo (Ctrl+Y)"]'));
  // }

  // get resetButton() {
  //   return element(by.css('button[title="Reset (Double-click)"]'));
  // }

  // get hideTranscriptsCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Hide transcripts')).get(0).element(by.css('input'));
  // }

  // get condenseIntronsCheckbox() {
  //   return element.all(by.cssContainingText('label', 'Condense introns')).get(0).element(by.css('input'));
  // }

  // get downloadButton() {
  //   return element(by.cssContainingText('button', /^Download$/));
  // }

  // get downloadSummaryButton() {
  //   return element(by.cssContainingText('button', 'Download Summary'));
  // }
}
