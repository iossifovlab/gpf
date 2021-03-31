import { BasePage } from './utils';

export class GenotypePreviewTablePage extends BasePage {
  get table() {
    return cy.get('gpf-genotype-preview-table');
  }

  getCellSpanElementsByIndex(index: number) {
    return cy.get('gpf-table gpf-table-view-cell').eq(index);
  }
}
