import { GenotypeBlockPage } from './genotype-block-page';
import { BasePage } from './utils';

export class GeneProfilesTablePage extends BasePage {
  public get window(): element {
    return cy.get('gpf-gene-profiles-table');
  }

  public get table(): element {
    return cy.get('.table-container');
  }

  public get aboveTableBar(): element {
    return cy.get('#above-table-bar');
  }

  public get categoryFilterButton(): element {
    return cy.get('#category-filtering-button');
  }

  public get allTableRows(): element {
    return cy.get('.table-body-row:not(#nothing-found)');
  }

  public get firstTableRow(): element {
    return this.allTableRows.first();
  }

  public get allTableCells(): element {
    return this.table.find('#table-body .row-cell');
  }

  public get secondTableCell(): element {
    return this.allTableCells.eq(1);
  }

  public get geneSearchInput(): element {
    return cy.get('#gene-search-input');
  }

  public get autismGeneSetColumnFilteringButton(): element {
    return cy.get('#autism_gene_sets_rank-column-filtering-button');
  }

  public get multipleSelectMenu(): element {
    return cy.get('gpf-multiple-select-menu');
  }

  public get multipleSelectMenuCheckUncheckAllButton(): element {
    return this.multipleSelectMenu.find('#check-uncheck-all-button');
  }

  public get multipleSelectMenuSearch(): element {
    return this.multipleSelectMenu.find('input[name="search"]');
  }

  public get allMultipleSelectMenuOptions(): element {
    return this.multipleSelectMenu.find('.cdk-drag');
  }

  public get allMultipleSelectMenuCheckboxes(): element {
    return this.multipleSelectMenu.find('label input');
  }

  public multipleSelectMenuCheckboxText(text: string): element {
    return this.multipleSelectMenu.find('label span').contains(text);
  }

  public get allSortingButtons(): element {
    return cy.get('gpf-sorting-buttons');
  }

  public get compareGenesModal() : element {
    return cy.get('#compare-genes-modal');
  }

  public get legendCompareButton(): element {
    return cy.get('#compare-genes-menu > div > :nth-child(1)');
  }

  public get legendDismissButton(): element {
    return cy.get('#remove-highlights-button');
  }

  public get legendSelectedGenes(): element {
    return cy.get('#compare-genes-menu > span');
  }

  public get compareGeneItems(): element {
    return cy.get('.compare-gene-item');
  }

  public get allColumnHeaders(): element {
    return cy.get('.header-cell-content-span');
  }

  public columnHeader(columnName: string): element {
    return cy.get('.header-cell').contains(columnName);
  }

  public clickSortButton(columnName: string): void {
    cy.get('div').contains(columnName).then(column => {
      cy.wrap(column).parent().within(button => {
        cy.wrap(button).get('.sorting-button').eq(1).click();
      });
    });
  }

  public allGeneSetsFilterSets(names: string[]): void {
    cy.get('#column-filtering-dropdown').within(menu => {
      cy.wrap(menu).get('tr > td').each(row => {
        const found = names.find(name => name === row.text());
        if (found !== undefined && found !== null) {
          cy.wrap(row).click();
        }
      });
    });
  }

  public get nothingFound(): element {
    return cy.get('#nothing-found');
  }

  public get firstTabCloseButton(): element {
    return cy.get('nav span').contains('×').first();
  }

  public getStudyExpectedDataFromGenotype(variantStatistics): void {
    const genotypeBlockPage = new GenotypeBlockPage();

    const studyWrapper = {
      denovo_lgds: genotypeBlockPage.effectTypesGroups.get('LGDs'),
      denovo_missense: ['missense'],
      denovo_intron: ['intron']
    };
    const effectModelFromGenotypeWrapper = new Map<string, string>();
    for (const value in studyWrapper) {
      effectModelFromGenotypeWrapper.set(value, studyWrapper[value]);
    }

    cy.wrap(effectModelFromGenotypeWrapper.get(variantStatistics)).as('genotypeExpectedWrapper');
  }

  public getStudyActualDataFromGenotype(): void {
    const selectedEffects = [];

    cy.get('.effect-card > .card-block label').each(label => {
      cy.wrap(label).within(checkBox => {
        cy.wrap(checkBox).get('input').then(check => {
          cy.wrap(check).invoke('prop', 'checked').then(isCheck => {
            if (isCheck === true) {
              selectedEffects.push(label.text());
            }
          });
        });
      });
    });

    cy.wrap(selectedEffects).as('genotypeActualWrapper');
  }
}
