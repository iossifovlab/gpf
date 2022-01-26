import { BasePage } from './utils';

export class PhenoBrowserPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-pheno-browser');
  }

  public get searchInputBox(): element {
    return cy.get('input.form-control');
  }

  public get allTableRows(): element {
    return cy.get('gpf-table > div > div.ng-star-inserted');
  }

  public get tableDiv(): element {
    return cy.get('.col-lg-12');
  }

  public get instrumentsBox(): element {
    return cy.get('select.form-control');
  }

  public get headerCells(): element {
    return this.tableDiv.get('gpf-table-view-header-cell');
  }

  public get tableCells(): element {
    return this.tableDiv.get('gpf-table-view-cell');
  }

  public get tableRows(): element {
    return this.tableDiv.get('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted');
  }

  public get downloadInstrumentsButton(): element {
    return cy.get('a').contains('Download instruments');
  }
}
