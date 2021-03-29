import { BasePage } from './utils';

export class EnrichmenToolPage extends BasePage {
  get enrichmentToolWindow() {
    return cy.get('gpf-enrichment-tool');
  }

  get enrichmentModelsBlock() {
    return cy.get('gpf-enrichment-models-block');
  }

  get enrichmentTestButton() {
    return cy.get('gpf-enrichment-tool').contains('Enrichment Test');
  }

  get table() {
    return cy.get('.enrichment-table');
  }

//   // Calling element.all(by.css('tr[label="effectType"]')) would return 2 <tr> elements.
//   // The 'statusToRow' is used to determine which one of these two <tr> elements is going to be used,
//   // based off the affectedStatus argument
//   findTableField(affectedStatus: string, effectType: string, columnNumber: number) {
//     const statusToRow = {
//       'affected': 0,
//       'unaffected': 1
//     };

//     return (
//       element.all(by.css('tr[label="' + effectType + '"]'))
//       .get(statusToRow[affectedStatus])
//       .all(by.css('td > a'))
//       .get(columnNumber)
//     );
//   }
}
