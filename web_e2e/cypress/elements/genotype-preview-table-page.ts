import { BasePage } from './utils';

export class GenotypePreviewTablePage extends BasePage {
  get table() {
    return cy.get('gpf-genotype-preview-table');
  }

  getSpansInTableRowByIndex(index: number) {
    return cy.get('gpf-table gpf-table-view-cell').eq(index).find('gpf-genotype-preview-field span');
  }

  getSpansInTableRow(rowIndex: number, columnIndex: number) {
    rowIndex = (rowIndex === 1 ? 0 : rowIndex*8);
    return cy.get('gpf-table gpf-table-view-cell').eq(rowIndex + columnIndex).find('gpf-genotype-preview-field span');
  }
}
