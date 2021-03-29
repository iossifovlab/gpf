import { BasePage } from "./utils";

export class GenotypePreviewTablePage extends BasePage {
  get table() {
    return cy.get('gpf-genotype-preview-table');
  }

//   async getCellSpanElementsByRowAndColumn(row: number, column: number): Promise<ElementFinder[]> {
//     const allCellsInARow: ElementArrayFinder = element.all(by.css('gpf-table gpf-table-view-cell'));
//     const arrayOfSpans = allCellsInARow.get(column).all(by.css('gpf-genotype-preview-field span'));

//     return arrayOfSpans;
//   }
}
