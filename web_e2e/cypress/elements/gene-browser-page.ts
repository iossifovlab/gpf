import { GenePlotPage } from './gene-plot-page';
import { BasePage } from './utils';

export class GeneBrowserPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-gene-browser', {timeout: 35000});
  }

  public get geneSymbolsHeader(): element {
    return cy.get('div').contains('Gene Symbols');
  }

  public get searchInputBox(): element {
    return cy.get('gpf-gene-browser input#search-box');
  }

  public get goButton(): element {
    return cy.get('input[value=\'Go\']', {timeout: 35000});
  }

  public get codingOnlyCheckbox(): element {
    return cy.get('input#coding-only-checkbox');
  }

  public get filters(): element {
    return cy.get('#filters');
  }

  public get affectedStatusField(): element {
    return cy.get('div#affected-status-filters');
  }

  public get effectTypeFiltersField(): element {
    return cy.get('div#effect-types-filters');
  }

  public get inheritanceTypesFilter(): element {
    return cy.get('div#inheritance-types-filters');
  }

  public get variantTypesFilter(): element {
    return cy.get('div#variant-types-filters');
  }

  public getAffectedStatusCheckbox(affectedStatus: string): element {
    return cy.get('.filter-label span').contains(affectedStatus);
  }

  public getEffectTypesCheckbox(effectType: string): element {
    return cy.get('#effect-types-filters span').contains(effectType);
  }

  public getInheritanceTypes(inheritanceType: string): element {
    return cy.get('#inheritance-types-filters span').contains(inheritanceType);
  }

  public getVariantTypes(variantType: string): element {
    return cy.get('#variant-types-filters span').contains(variantType);
  }

  public get legend(): element {
    return cy.get('.legend-div');
  }

  public get downloadSummaryButton(): element {
    return cy.get('button').contains('Download Summary');
  }

  public get downloadButton(): element {
    return cy.get('#download-button');
  }

  public clickGoButton(): void {
    const genePlotPage = new GenePlotPage();
    this.goButton.click();
    genePlotPage.window.should('be.visible');

    // this.goButton.click({timeout: this.longerDefaultTimeout}).then(() => {
    //   genePlotPage.window.should('be.visible')
    // });
    // cy.wrap(this.goButton.click(), {timeout: 35000}).then(()=> true);
  }
}
