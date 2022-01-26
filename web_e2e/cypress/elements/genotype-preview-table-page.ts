import { BasePage } from './utils';

export class GenotypePreviewTablePage extends BasePage {
  public get table(): element {
    return cy.get('gpf-genotype-preview-table');
  }

  public getSpansInTableRowByIndex(index: number): element {
    return cy.get('gpf-table gpf-table-view-cell').eq(index).find('gpf-genotype-preview-field span');
  }

  public ggetSpansInTableRow(rowIndex: number, columnIndex: number): element {
    rowIndex = (rowIndex === 1 ? 0 : rowIndex*8);
    return cy.get('gpf-table gpf-table-view-cell').eq(rowIndex + columnIndex).find('gpf-genotype-preview-field span');
  }
}
