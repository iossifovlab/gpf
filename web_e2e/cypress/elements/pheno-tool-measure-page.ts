import { BasePage } from './utils';

export class PhenoToolMeasurePage extends BasePage {
  public get block(): element {
    return cy.get('gpf-pheno-tool-measure');
  }

  public get searchbox(): element {
    return this.block.find('input#tags');
  }

  public get ageCheckbox(): element {
    return cy.contains('Age').find('input');
  }

  public get iqCheckbox(): element {
    return cy.contains('Non verbal IQ').find('input');
  }

  public getCheckboxByText(text: string): element {
    return cy.get('span').contains(text).parent();
  }

  public get dropdown(): element {
    return cy.get('.ui-front');
  }

  public getDropdownOptionByText(text: string): element {
    return cy.get('.ui-menu-item-wrapper').contains(text);
  }

  public get fromInputField(): element {
    return cy.get('#from-input-field');
  }

  public get toInputField(): element {
    return cy.get('#to-input-field');
  }
}
