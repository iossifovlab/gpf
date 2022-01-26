import { GenotypeBlockPage } from './genotype-block-page';
import { BasePage } from './utils';

export class AutismGeneProfilesTable extends BasePage {
  public get window(): element {
    return cy.get('gpf-autism-gene-profiles-table');
  }

  public get table(): element {
    return cy.get('gpf-autism-gene-profiles-table table');
  }

  public get allTableCells(): element {
    return this.table.find('tbody td');
  }

  public get allTableRows(): element {
    return this.table.find('tbody tr');
  }

  public get firstGeneInTable(): element {
    return this.allTableCells.first();
  }

  public get geneSearchInput(): element {
    return cy.get('#gene-search-input');
  }

  public get autismGeneSetsButton(): element {
    return cy.get('#autism_gene_sets-button');
  }

  public get autismGeneSetsDropdown(): element {
    return cy.get('#autism_gene_sets-dropdown');
  }

  public get autismGeneSetsCheckUncheckAllButton(): element {
    return this.autismGeneSetsDropdown.find('#check-uncheck-all-button');
  }

  public get autismGeneSetsDropdownSearch(): element {
    return this.autismGeneSetsDropdown.find('input[name="search"]');
  }

  public get autismGeneSetsDropdownApplyButton(): element {
    return this.autismGeneSetsDropdown.contains('Apply');
  }

  public get allAutismGeneSetsDropdownCheckboxes(): element {
    return this.autismGeneSetsDropdown.find('label input');
  }

  public get allSortingButtons(): element {
    return cy.get('gpf-sorting-buttons');
  }

  public get allGeneSetsDropdownButton(): element {
    return cy.get('#column-filtering-button');
  }
  
  public get legend() : element{
    return cy.get('div#compare-genes-menu');
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

  public clickSortButton(columnName: string): void {
    cy.get('th').contains(columnName).then(column => {
      cy.wrap(column).parent().within(button => {
        cy.wrap(button).get('.clickable').click();
      });
    });
  }

  public allGeneSetsClickApplyButton(): void {
    cy.get('#column-filtering-dropdown').within(menu => {
      cy.wrap(menu).get('button.btn-secondary').click();
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

  public get searchResultWarning(): element {
    return cy.get('#search-warning > td > span');
  }

  public get firstTabCloseButton(): element {
    return cy.get('nav span').contains('×').first();
  }

  public getStudyExpectedDataFromGenotype(variantStatistics: any): void {
    const genotypeBlockPage = new GenotypeBlockPage();

    const studyWrapper = {
      'denovo_lgds': genotypeBlockPage.effectTypesGroups.get('LGDs'),
      'denovo_missense': [ 'Missense' ],
      'denovo_intron': [ 'Intron' ]
    }
    let effectModelFromGenotypeWrapper = new Map<String, String>();
    for(var value in studyWrapper) {
      effectModelFromGenotypeWrapper.set(value, studyWrapper[value]);
    }

    cy.wrap(effectModelFromGenotypeWrapper.get(variantStatistics)).as('genotypeExpectedWrapper');
  }

  public getStudyActualDataFromGenotype(): void {
    let selectedEffects = [];

    cy.get('.effect-card > .card-block label').each(label => {
      cy.wrap(label).within(checkBox => {
        cy.wrap(checkBox).get('input').then(check => {
          cy.wrap(check).invoke('prop', 'checked').then(isCheck => {
            if(isCheck === true) {
              selectedEffects.push(label.text());
            }
          });
        });
      });
    });
    
    cy.wrap(selectedEffects).as('genotypeActualWrapper');
  }
}
