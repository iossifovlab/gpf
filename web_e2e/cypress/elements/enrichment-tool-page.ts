import { BasePage } from './utils';

export class EnrichmentToolPage extends BasePage {
  get enrichmentToolWindow() {
    return cy.get('gpf-enrichment-tool');
  }

  get enrichmentModelsBlock() {
    return cy.get('gpf-enrichment-models-block');
  }

  get enrichmentTestButton() {
    return cy.get('gpf-enrichment-tool input[value="Enrichment Test"');
  }

  get table() {
    return cy.get('.enrichment-table');
  }

  findTableField(affectedStatus: string, effectType: string, columnNumber: number) {
    const statusToRow = {'affected': 0, 'unaffected': 1};
    return cy.get(`tr[label="${effectType}"]`).eq(statusToRow[affectedStatus]).find(('td')).eq(columnNumber);
  }

  selectorTableRow(affectedStatus: string) {
    return cy.get('.selector-cell').eq(affectedStatus === 'affected' ? 1 : 2);
  }

  enrichmentModelsSelector(modelName: string) {
    let element = cy.get('select');
    this.enrichmentModelsBlock.then(() => {
      if (modelName === 'background') {
        element = cy.get('select').eq(0);
      } else if (modelName === 'counting') {
        element = cy.get('select').eq(1);
      }
    });
    return element;
  }
}
