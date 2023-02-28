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

  public get familiesByPedigreeTable(): element {
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

  public get pedigreeLegendDropdownElements(): element {
    return cy.get('#legend-items-wrapper').children('.legend-item');
  }

  public get denovoTagSelectorDropdown(): element {
    return cy.get('span.dropdown-btn');
  }

  public get denovoTagSelectorContent(): element {
    return cy.get('.dropdown-list');
  }

  public get denovoTagSelectorSearch(): element {
    return cy.get('ul.item1');
  }

  public get denovoTagSelectorOptions(): element {
    return cy.get('ul.item2').children('li');
  }

  public denovoTagSelectorOptionsInput(label: string): element {
    return cy.get('input[aria-label="'+label+'"]');
  }

  public get denovoTagSelectorSelectedOptions(): element {
    return cy.get('span.dropdown-btn');
  }

  public get denovoTagSelectorSelectedOptionRemoveBtn(): element {
    return cy.get('.selected-item a');
  }

  public get pedigreeCells(): element {
    return cy.get('.pedigree-cell');
  }

  public get denovoTagSelectorSearchInput(): element {
    return cy.get('input[aria-label="multiselect-search"]');
  }

  public get denovoTagSelectorSearchInputNothingFound(): element {
    return cy.get('.no-filtered-data');
  }

  public get pedigreesNothingFound(): element {
    return cy.get('#nothing-found');
  }

  public get pedigreeModalContent(): element {
    return cy.get('.modal-content');
  }

  public get pedigreeModalChart(): element {
    return cy.get('#modal-pedigree-container');
  }

  public get pedigreeModalCount(): element {
    return cy.get('#modal-family-count');
  }

  public get pedigreeModalDownloadBtn(): element {
    return cy.get('.modal-family #download-button');
  }

  public get pedigreeModalFamilyIds(): element {
    return cy.get('#family-ids-list > div');
  }
}
