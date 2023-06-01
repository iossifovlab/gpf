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

  public get downloadAllFamilies(): element {
    return cy.get('#download-total-families');
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

  public get dropdown(): element {
    return cy.get('#families-by-pedigree-select');
  }

  public get openPedigreeTagsModal(): element {
    return cy.get('#open-modal-button');
  }

  public get pedigreeTagsModal(): element {
    return cy.get('#tags-modal-content');
  }

  public get pedigreeTagsModalSearch(): element {
    return cy.get('#search-tags');
  }

  public get pedigreeTagsModalUncheckAll(): element {
    return cy.get('#uncheck-button');
  }

  public get pedigreeTagsModalTags(): element {
    return cy.get('#tag-list');
  }

  public findTag(tag: string): element {
    return cy.get('label').contains(tag);
  }

  public findTagCheckbox(tag: string): element {
    return cy.get(`#${tag}-tag`);
  }

  public get selectedTagsHeader(): element {
    return cy.get('#selected-tags-list');
  }

  public get pedigreeCells(): element {
    return cy.get('.pedigree-cell');
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

  public get familiesByPedigreeSelectOptions(): element {
    return cy.get('#families-by-pedigree-select').children('option');
  }
}
