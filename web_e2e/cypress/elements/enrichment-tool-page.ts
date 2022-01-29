import { BasePage } from './utils';

export class EnrichmentToolPage extends BasePage {
  public get enrichmentModelsBlock(): element {
    return cy.get('gpf-enrichment-models-block');
  }

  public get enrichmentTestButton(): element {
    return cy.get('gpf-enrichment-tool input[value="Enrichment Test"]');
  }

  public get table(): element {
    return cy.get('.enrichment-table');
  }

  private findTableRow(affectedStatus: string, effectType: string): element {
    const statusToRow = {
      affected: 0,
      unaffected: 1
    };

    return cy.get(`tr[label="${effectType}"]`).eq(statusToRow[affectedStatus]);
  }

  public async getRowValues(affectedStatus: string, effectType: string): Promise<string[]> {
    return new Cypress.Promise(resolve => {
      const result: string[] = [];
      this.findTableRow(affectedStatus, effectType).find('td')
        .each(td => {
          result.push(td.text());
        })
        .then(() => {
          result.shift();
          return resolve(result);
        })
    });
  }

  public findTableCell(affectedStatus: string, effectType: string, columnNumber: number): element {
    return this.findTableRow(affectedStatus, effectType).find(('td')).eq(columnNumber);
  }
}
