import { BasePage } from './utils';

export class DatasetsPage extends BasePage {
  get datasetStatisticsWindow() {
    return cy.get('gpf-variant-reports');
  }

  get permissionDeniedPrompt() {
    return cy.get('#permission-denied-prompt');
  }

  get datasetsDropdownMenuButton() {
    return cy.get('#datasets-dropdown-menu-button');
  }

  get datasetStatisticsButton() {
    return cy.get('a.nav-link').contains('Dataset Statistics');
  }

  get genotypeBrowserButton() {
    return cy.get('a.nav-link').contains('Genotype Browser');
  }

  get phenotypeBrowserButton() {
    return cy.get('a.nav-link').contains('Phenotype Browser');
  }

  get phenotypeToolButton() {
    return cy.get('a.nav-link').contains('Phenotype Tool');
  }

  get familiesByNumberDropdownButton() {
    return cy.get('#families-by-number-dropdown-button');
  }

  getFamiliesByNumberDropdownOptionByText(text: string) {
    return cy.get('#families-by-number-dropdown-button option').contains(text);
  }

//   async getFamiliesByNumberColumnElementsByRoleId(roleId: string): Promise<ElementFinder[]> {
//     let columnElementsByRoleId: ElementFinder[];

//     const allTableTdElements = await element.all(by.css('div#families-by-number-div td'));
//     const tableHeaderElements = await (element.all(by.css('div#families-by-number-div tbody th'))).getText();
//     const indexOfRoleId = tableHeaderElements.indexOf(roleId);

//     columnElementsByRoleId = [
//       allTableTdElements[indexOfRoleId * 3],
//       allTableTdElements[indexOfRoleId * 3 + 1],
//       allTableTdElements[indexOfRoleId * 3 + 2],
//     ];

//     return columnElementsByRoleId;
//   }

//   async getFamiliesByPedigreeValues(): Promise<number[]> {
//     const tableCellElements: ElementFinder[] = await element.all(by.css('gpf-common-reports-pedigree-cell > div > div'));
//     const finalValues: number[] = [];
//     let singleCellValue;

//     for (const cell of tableCellElements) {
//       singleCellValue = (await cell.getText()).split(',');
//       if (singleCellValue.length !== 1) {
//         for (const v of singleCellValue) {
//           finalValues.push(Number(v));
//         }
//       } else {
//         finalValues.push(Number(singleCellValue));
//       }
//     }

//     return finalValues.filter((e) => e !== 0);
//   }

  getDenovoTableHeaderElements() {
    return cy.get('div#denovo-variants-div thead div');
  }

//   async findDenovoVariantsCountsByRowName(rowName: string): Promise<ElementFinder[]> {
//     const denovoVariantsCount: ElementFinder[] =
//       await (element(by.cssContainingText('div#denovo-variants-div th', rowName)).element(by.xpath('..')).all(by.css('div')));

//     return denovoVariantsCount;
//   }

  get denovoVariantsDropdownButton() {
    return cy.get('#denovo-variants-dropdown-button');
  }

  getDenovoVariantsDropdownOptionByText(text: string) {
    return cy.get('#denovo-variants-dropdown-button option').contains(text);
  }
}
