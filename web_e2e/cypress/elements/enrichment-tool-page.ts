import { BasePage } from './utils';

export class EnrichmentToolPage extends BasePage {
  get enrichmentToolWindow() {
    return cy.get('gpf-enrichment-tool');
  }

  get enrichmentModelsBlock() {
    return cy.get('gpf-enrichment-models-block');
  }

  get enrichmentTestButton() {
    return cy.get('gpf-enrichment-tool input[value="Enrichment Test"]');
  }

  get table() {
    return cy.get('.enrichment-table');
  }

  findTableRow(affectedStatus: string, effectType: string) {
    const statusToRow = {
      'affected': 0,
      'unaffected': 1
    };

    return cy.get(`tr[label="${effectType}"]`).eq(statusToRow[affectedStatus]);
  }

  async getRowValues(affectedStatus: string, effectType: string): Promise<string[]> {
    return new Cypress.Promise((resolve) => {
      let result: string[] = [];
      this.findTableRow(affectedStatus, effectType).find('td')
      .each(td => {
        result.push(td.text());
        console.log(result);
      })
      .then(() => {
        result.shift();
        return resolve(result);
      })
    });
  }

  findTableCell(affectedStatus: string, effectType: string, columnNumber: number) {
    return this.findTableRow(affectedStatus, effectType).find(('td')).eq(columnNumber);
  }
}
