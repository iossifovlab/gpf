import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles table tests', () => {
  const page = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display table', () => {
    page.table.should('be.visible');
  });

  it('should display gene search bar', () => {
    page.geneSearchInput.should('be.visible');
  });

  it('should filter out genes via the gene search ', () => {
    page.geneSearchInput.type('CHD8');
    page.allTableRows.should('have.length', 1);
  });

  it('should display gene sets columns filtering button', () => {
    page.autismGeneSetsButton.should('be.visible');
  });

  // tests for the other columns filtering buttons
});

describe('Autism gene profiles table data tests', () => {
  const page = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  [{geneSymbol: 'CHD8', expectedRow: ['CHD8', '✓', '✓', '', '✓', '✓', '✓', '1', '193', '83', '31.5', '18178', '7 (2.792)', '', '', '', '', '']},
   {geneSymbol: 'SHANK2', expectedRow: ['SHANK2', '✓', '✓', '', '', '', '✓', '2', '', '43', '649', '17517', '1 (0.399)', '', '', '', '1 (0.524)', '']},
   {geneSymbol: 'FLG', expectedRow: ['FLG', '', '', '', '', '✓', '', '', '16640', '18394.5', '', '', '1 (0.399)', '', '', '', '', '']},
   {geneSymbol: 'CMIP', expectedRow: ['CMIP', '', '', '✓', '', '', '', '7', '558', '2494', '694', '17467', '', '', '', '', '', '']},
   {geneSymbol: 'TBCD', expectedRow: ['TBCD', '', '', '✓', '', '', '', '', '646', '9111.5', '13275.5', '222', '', '', '', '', '1 (0.524)', '2 (1.047)']},
  ].forEach((data) => {
    it(`should display correct gene data for ${data.geneSymbol}`, () => {
      page.geneSearchInput.type(data.geneSymbol);
      page.allTableRows.should('have.length', 1);
      
      for (let cellIndex = 0; cellIndex < data.expectedRow.length; cellIndex++) {
        page.allTableRows.find('td').eq(cellIndex).should('have.text', data.expectedRow[cellIndex]);
      }
    });
  });
});

describe('Column filtering dropdown tests', () => {
  const page = new AutismGeneProfilesTable();

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
    page.autismGeneSetsButton.click();
  });

  it('should open autism gene sets dropdown after clicking on the autism gene sets columns filtering button', () => {
    page.autismGeneSetsDropdown.should('be.visible');
  });

  it('should open gene sets dropdown and display the check/uncheck all button', () => {
    page.autismGeneSetsCheckUncheckAllButton.should('be.visible');
  });

  it('should open gene sets dropdown and display the search input box', () => {
    page.autismGeneSetsDropdownSearch.should('be.visible');
  });

  it('should open gene sets dropdown and display the appply button', () => {
    page.autismGeneSetsDropdownApplyButton.should('be.visible');
  });

  it('should check/uncheck all gene sets column filtering options using the check/uncheck all button', () => {
    page.allAutismGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('be.checked');
    });
    page.autismGeneSetsCheckUncheckAllButton.click();
    page.allAutismGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('not.be.checked');
    });
    page.autismGeneSetsCheckUncheckAllButton.click();
    page.allAutismGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });

  it('should change the check/uncheck button text', () => {
    page.autismGeneSetsCheckUncheckAllButton.should('have.text', 'Uncheck all');

    page.autismGeneSetsCheckUncheckAllButton.click();
    page.autismGeneSetsCheckUncheckAllButton.should('have.text', 'Check all');

    page.autismGeneSetsCheckUncheckAllButton.click();
    page.autismGeneSetsCheckUncheckAllButton.should('have.text', 'Uncheck all');
  });

  it('should filter gene sets dropdown options using the search', () => {
    page.allAutismGeneSetsDropdownCheckboxes.should('have.length', 2);
    page.autismGeneSetsDropdownSearch.type('iossifov');
    page.allAutismGeneSetsDropdownCheckboxes.should('have.length', 1);
  });

  it('should test statistic to genotype browser test', () => {
    page.loginAdmin();

    cy.intercept({
      method: 'POST',
      url: '/gpf/api/v3/query_state/save'
    }).as('query');
    cy.get('tr:nth-child(1) > :nth-child(13) > .link-td > .link-span').click({force:true});
    cy.wrap('denovo_lgds').as('effectType');
    cy.wait('@query');
    cy.get('@query').then(req => {
      if(req !== null) {
        const genotypeBlockPage = new GenotypeBlockPage();
        cy.visit(Cypress.config().baseUrl + '/load-query/' + req.response.body.uuid);
        genotypeBlockPage.findCheckboxInComponentContainingText('.pedigree-selector-card', 'affected').parent().within(checkBoxes => {
          cy.wrap(checkBoxes).get('input').should('be.checked');
          cy.get('@effectType').then(effectType => {
            page.getStudyExpectedDataFromGenotype(effectType);
          });
        });
        page.getStudyActualDataFromGenotype();
        cy.get('@genotypeExpectedWrapper').then(expected => {
          cy.get('@genotypeActualWrapper').then(actual => {
            expect(expected).to.deep.equal(actual);
          });
        });
      }
    });
  });

  it('should check if columns can be removed/added', () => {
    cy.get('th.table-main-header').should('have.length', 6);

    page.allGeneSetsDropdownButton.click();
    page.allGeneSetsFilterSets(['autism_scores' ,'autism_gene_sets']);
    page.allGeneSetsClickApplyButton();

    cy.get('th.table-main-header').should('have.length', 4);
  });

  // apply should actually work and make columns disappear/add

  // sorting should work

  // sorting arrow should change the image when clicked
});
