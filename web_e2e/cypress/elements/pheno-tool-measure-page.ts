import { BasePage } from './utils';

export class PhenoToolMeasurePage extends BasePage {
  public get block(): element {
    return cy.get('gpf-pheno-tool-measure');
  }

  public get searchbox(): element {
    return cy.get('gpf-pheno-tool-measure input#search-box');
  }

  public get ageCheckbox(): element {
    return cy.contains('Age').find('input');
  }

  public get iqCheckbox(): element {
    return cy.contains('Non verbal IQ').find('input');
  }

  public get dropdown(): element {
    return cy.get('.dropdown-menu');
  }

  public getDropdownOptionByText(text: string): element {
    return this.dropdown.find('span').contains(text);
  }

  public get clearMeasureButton(): element {
    return cy.get('#clear-measure-button');
  }

  public get fromInputField(): element {
    return cy.get('#from-input-field');
  }

  public get toInputField(): element {
    return cy.get('#to-input-field');
  }
}
