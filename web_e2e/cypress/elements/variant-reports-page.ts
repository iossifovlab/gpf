import { BasePage } from './utils';

export class VariantReportsPage extends BasePage {
  public get familiesByNumberTab(): element {
    return cy.get('a').contains('Families by number');
  }

  public get familiesByPedigreeTab(): element {
    return cy.get('a').contains('Families by pedigree');
  }

  public get deNovoVariantsTab(): element {
    return cy.get('a').contains('De Novo variants');
  }

  public get totalNumberOfFamilies(): element {
    return cy.get('#total-number-of-families');
  }

  public get downloadAllLink(): element {
    return cy.get('.download-link');
  }

  public get familiesByNumberSelect(): element {
    return cy.get('#families-by-number-select');
  }

  public get familiesByPedigreeSelect(): element {
    return cy.get('#families-by-pedigree-select');
  }

  public get familiesByPedigreeSelectOptions(): element {
    return cy.get('#families-by-pedigree-select').children('option');
  }

  public get denovoVariantsSelect(): element {
    return cy.get('#denovo-variants-select');
  }

  public get familiesByNumber(): element {
    return cy.get('#families-by-number-div');
  }

  public get allFamiliesByNumberHeaderCells(): element {
    return cy.get('div#families-by-number-div tbody th');
  }

  public get allFamiliesByNumberDataCells(): element {
    return cy.get('div#families-by-number-div td');
  }

  public get familiesByPedigree(): element {
    return cy.get('#families-by-pedigree-div');
  }

  public get familiesByPedigreeDownloadButton(): element {
    return cy.get('#download-button');
  }

  public get familiesByPedigreeDivs(): element {
    return cy.get('gpf-common-reports-pedigree-cell .pedigree-count');
  }

  public get denovoVariants():element {
    return cy.get('#denovo-variants-div');
  }

  public findDenovoVariantsCountsByRowName(rowName: string): element {
    return cy.get('div#denovo-variants-div th').contains(rowName).parent().find('div');
  }

  public get denovoTagSelector(): element {
    return cy.get('#tags-selector');
  }

  public get denovoLegend(): element {
    return cy.get('#de-novo-variants-legend-report');
  }

  public get pedigreeLegendButton(): element {
    return cy.get('button#expand-legend-button');
  }

  public get pedigreeLegendDropdown(): element {
    return cy.get('div#legend');
  }
}
