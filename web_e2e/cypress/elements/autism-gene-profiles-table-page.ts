import { GenotypeBlockPage } from './genotype-block-page';
import { BasePage } from './utils';

export class AutismGeneProfilesTable extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profiles-table');
  }

  get table() {
    return cy.get('gpf-autism-gene-profiles-table table');
  }

  get allTableCells() {
    return this.table.find('tbody td');
  }

  get allTableRows() {
    return this.table.find('tbody tr');
  }

  get firstGeneInTable() {
    return this.allTableCells.first();
  }

  get geneSearchInput() {
    return cy.get('#gene-search-input');
  }

  get autismGeneSetsButton() {
    return cy.get('#autism_gene_sets-button');
  }

  get autismGeneSetsDropdown() {
    return cy.get('#autism_gene_sets-dropdown');
  }

  get autismGeneSetsCheckUncheckAllButton() {
    return this.autismGeneSetsDropdown.find('#check-uncheck-all-button');
  }

  get autismGeneSetsDropdownSearch() {
    return this.autismGeneSetsDropdown.find('input[name="search"]');
  }

  get autismGeneSetsDropdownApplyButton() {
    return this.autismGeneSetsDropdown.contains('Apply');
  }

  get allAutismGeneSetsDropdownCheckboxes() {
    return this.autismGeneSetsDropdown.find('label input');
  }

  get allSortingButtons() {
    return cy.get('gpf-sorting-buttons');
  }

  get allGeneSetsDropdownButton() {
    return cy.get('#column-filtering-button');
  }

  clickSortButton(columnName: string) {
    cy.get('th').contains(columnName).then(column => {
      cy.wrap(column).parent().within(button => {
        cy.wrap(button).get('.clickable').click({force:true});
      });
    });
  }

  allGeneSetsClickApplyButton() {
    cy.get('#column-filtering-dropdown').within(menu => {
      cy.wrap(menu).get('button.btn-secondary').click();
    });
  }

  allGeneSetsFilterSets(names: String[]) {
    cy.get('#column-filtering-dropdown').within(menu => {
      cy.wrap(menu).get('tr > td').each(row => {
        const found = names.find(name => name === row.text());
        if(found !== undefined && found !== null) {
          cy.wrap(row).click();
        }
      });
    });
  }

  get searchResultWarning() {
    return cy.get('#search-warning > td > span');
  }

  get firstTabCloseButton() {
    return cy.get('nav span').contains('×').first();
  }

  getStudyExpectedDataFromGenotype(variantStatistics: any) {
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

  getStudyActualDataFromGenotype() {
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
