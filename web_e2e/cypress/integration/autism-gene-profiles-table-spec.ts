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
});

describe('Autism gene profiles table row data tests', () => {
  const page = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  [
    {geneSymbol: 'CHD8', expectedRow: ['CHD8', '✓', '✓', '', '✓', '✓', '✓', '1', '193', '83', '31.5', '18178', '7 (2.792)', '', '', '', '', '']},
    {geneSymbol: 'SHANK2', expectedRow: ['SHANK2', '✓', '✓', '', '', '', '✓', '2', '', '43', '649', '17517', '1 (0.399)', '', '', '', '1 (0.524)', '']},
    {geneSymbol: 'FLG', expectedRow: ['FLG', '', '', '', '', '✓', '', '', '16640', '18394.5', '', '', '1 (0.399)', '', '', '', '', '']},
    {geneSymbol: 'CMIP', expectedRow: ['CMIP', '', '', '✓', '', '', '', '7', '558', '2494', '694', '17467', '', '', '', '', '', '']},
    {geneSymbol: 'TBCD', expectedRow: ['TBCD', '', '', '✓', '', '', '', '', '646', '9111.5', '13275.5', '222', '', '', '', '', '1 (0.524)', '2 (1.047)']}
  ].forEach(data => {
    it(`should display correct gene data for ${data.geneSymbol}`, () => {
      page.geneSearchInput.type(data.geneSymbol);
      page.allTableRows.should('have.length', 1);

      for (let cellIndex = 0; cellIndex < data.expectedRow.length; cellIndex++) {
        page.allTableRows.find('td').eq(cellIndex).should('have.text', data.expectedRow[cellIndex]);
      }
    });
  });
});

describe('Autism gene profiles table column filtering dropdown tests', () => {
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
    page.allAutismGeneSetsDropdownCheckboxes.each(element => {
      cy.wrap(element).should('be.checked');
    });
    page.autismGeneSetsCheckUncheckAllButton.click();
    page.allAutismGeneSetsDropdownCheckboxes.each(element => {
      cy.wrap(element).should('not.be.checked');
    });
    page.autismGeneSetsCheckUncheckAllButton.click();
    page.allAutismGeneSetsDropdownCheckboxes.each(element => {
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

  it('should check if columns can be removed/added', () => {
    cy.get('th.table-main-header').should('have.length', 6);

    page.allGeneSetsDropdownButton.click();
    page.allGeneSetsFilterSets(['autism_scores', 'autism_gene_sets']);
    page.allGeneSetsClickApplyButton();

    cy.get('th.table-main-header').should('have.length', 4);
  });
});

describe('Autism gene profiles table row highlight tests', () => {
  const page = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should highlight a row using control+click and change it\'s the background color', () => {
    page.allTableRows.eq(0).should('not.have.class', 'row-highlight');

    page.allTableRows.eq(0).click({ctrlKey: true});
    page.allTableRows.eq(0).should('have.class', 'row-highlight');
    page.allTableRows.eq(0).should('have.css', 'background-color').and('eq', 'rgb(255, 255, 214)');

    page.allTableRows.eq(0).click({ctrlKey: true});
    page.allTableRows.eq(0).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(0).should('not.have.property', 'background-color');
  });

  it('should highlight a several rows and check whether background color is different for odd and even rows', () => {
    page.allTableRows.eq(0).click({ctrlKey: true});
    page.allTableRows.eq(1).click({ctrlKey: true});
    page.allTableRows.eq(2).click({ctrlKey: true});
    page.allTableRows.eq(3).click({ctrlKey: true});
    page.allTableRows.eq(4).click({ctrlKey: true});

    page.allTableRows.eq(0).should('have.css', 'background-color').and('eq', 'rgb(255, 255, 214)');
    page.allTableRows.eq(1).should('have.css', 'background-color').and('eq', 'rgb(247, 247, 203)');
    page.allTableRows.eq(2).should('have.css', 'background-color').and('eq', 'rgb(255, 255, 214)');
    page.allTableRows.eq(3).should('have.css', 'background-color').and('eq', 'rgb(247, 247, 203)');
    page.allTableRows.eq(4).should('have.css', 'background-color').and('eq', 'rgb(255, 255, 214)');
  });

  it('should highlight the first 3 rows and then press escape to remove all highlights', () => {
    page.allTableRows.eq(0).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(1).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(2).should('not.have.class', 'row-highlight');

    page.allTableRows.eq(0).click({ctrlKey: true});
    page.allTableRows.eq(1).click({ctrlKey: true});
    page.allTableRows.eq(2).click({ctrlKey: true});

    page.allTableRows.eq(0).should('have.class', 'row-highlight');
    page.allTableRows.eq(1).should('have.class', 'row-highlight');
    page.allTableRows.eq(2).should('have.class', 'row-highlight');

    cy.get('body').type('{esc}');
    page.allTableRows.eq(0).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(1).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(2).should('not.have.class', 'row-highlight');
  });
});

describe('Autism gene profiles table functionality tests', () => {
  const page = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should test statistic to genotype browser test', () => {
    page.loginAdmin();

    cy.intercept({
      method: 'POST',
      url: '/gpf/api/v3/query_state/save'
    }).as('query');
    page.geneSearchInput.type('CHD8');
    page.allTableRows.should('have.length', 1);
    cy.get('tr.ng-star-inserted > :nth-child(13)').click();
    cy.wrap('denovo_lgds').as('effectType');
    cy.wait('@query');
    cy.get('@query').then(req => {
      if (req !== null) {
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

  it('should sort genes by autism gene sets', () => {
    page.geneSearchInput.type('RAPGEF');
    page.allTableRows.should('have.length', 4);

    const dataArr = [[0, 0, 1], [0, 0, 0], [0, 0, 0], [1, 0, 0]];

    page.allSortingButtons.eq(0).click();
    dataArr.forEach((allRows, allRowsIndex) => {
      allRows.forEach((rowData, rowIndex) => {
        page.allTableRows.eq(allRowsIndex).within(row => {
          cy.wrap(row).get('td').eq(rowIndex+1).should('have.text', rowData === 1 ? '✓' : '');
        });
      });
    });

    dataArr.sort((a, b) => b[0] - a[0]);

    page.allSortingButtons.eq(0).click();
    dataArr.forEach((allRows, allRowsIndex) => {
      allRows.forEach((rowData, rowIndex) => {
        page.allTableRows.eq(allRowsIndex).within(row => {
          cy.wrap(row).get('td').eq(rowIndex+1).should('have.text', rowData === 1 ? '✓' : '');
        });
      });
    });
  });

  it('should sort genes by relevant gene sets', () => {
    page.geneSearchInput.type('RAPGEF');
    page.allTableRows.should('have.length', 4);

    page.clickSortButton('Relevant Gene Sets');
    page.allTableRows.should('have.length', 4);

    const dataArr = [
      [1, 0, 1, 1],
      [0, 0, 1, 1],
      [0, 0, 0, 1],
      [0, 0, 0, 1]
    ];

    dataArr.forEach((allRows, allRowsIndex) => {
      allRows.forEach((rowData, rowIndex) => {
        page.allTableRows.eq(allRowsIndex).within(row => {
          cy.wrap(row).get('td').eq(rowIndex + 3).should('have.text', rowData === 1 ? '✓' : '');
        });
      });
    });

    page.clickSortButton('Relevant Gene Sets');
    page.allTableRows.should('have.length', 4);

    dataArr.reverse();
    dataArr.forEach((allRows, allRowsIndex) => {
      allRows.forEach((rowData, rowIndex) => {
        page.allTableRows.eq(allRowsIndex).within(row => {
          cy.wrap(row).get('td').eq(rowIndex+3).should('have.text', rowData === 1 ? '✓' : '');
        });
      });
    });
  });

  it('should test autism scores', () => {
    page.geneSearchInput.type('CHD');
    page.allTableRows.should('have.length', 15);

    page.clickSortButton('SFARI_gene_score');

    const dataArr = [2, 1, null];
    dataArr.forEach((rowData, allRowsIndex) => {
      page.allTableRows.should('have.length', 15);
      page.allTableRows.eq(allRowsIndex).within(row => {
        cy.wrap(row).get('td').eq(7).should('have.text', rowData === null ? '' : rowData);
      });
    });

    dataArr.reverse();
    page.clickSortButton('SFARI_gene_score');

    dataArr.forEach((rowData, allRowsIndex) => {
      page.allTableRows.should('have.length', 15);
      page.allTableRows.eq(allRowsIndex).within(row => {
        cy.wrap(row).get('td').eq(7).should('have.text', rowData === null ? '' : rowData);
      });
    });
  });

  it('should compare protection scores', () => {
    page.geneSearchInput.type('RAPGEF');
    page.allTableRows.should('have.length', 4);

    [
      ['RVIS_rank', 2208.5, 449, 2187.5, 383],
      ['LGD_rank', 10012.5, 1838.5, 737, 299.5],
      ['pLI_rank', 3433, 374, 2574, 659],
      ['pRec_rank', 13429, 17823, 14843, 17507]
    ].forEach((dataArray, columnIndex) => {
      page.clickSortButton(dataArray[0]);
      const valuesArray = dataArray.splice(1);
      valuesArray.sort((a, b) => b - a);
      valuesArray.forEach((rowData, rowIndex) => {
        page.allTableRows.should('have.length', 4);
        page.allTableRows.eq(rowIndex).within(row => {
          cy.wrap(row).get('td').eq(8 + columnIndex).should('have.text', rowData);
        });
      });

      page.clickSortButton(dataArray[0]);
      valuesArray.sort((a, b) => a - b);
      valuesArray.forEach((rowData, rowIndex) => {
        page.allTableRows.should('have.length', 4);
        page.allTableRows.eq(rowIndex).within(row => {
          cy.wrap(row).get('td').eq(8 + columnIndex).should('have.text', rowData);
        });
      });
    });
  });

  it('should show nothing found when search query dosent match', () => {
    page.searchResultWarning.should('not.exist');

    page.geneSearchInput.type('non-existing-gene');
    page.searchResultWarning.should('be.visible');
    page.searchResultWarning.should('have.text', 'Nothing found');

    page.geneSearchInput.clear();
    page.allTableRows.should('have.length.above', 1);
    page.searchResultWarning.should('not.exist');
  });

  it('should use home/end buttons functionality', () => {
    page.geneSearchInput.type('CHD');
    page.allTableRows.should('have.length', 15);

    cy.scrollTo('bottom');
    cy.window().its('scrollY').then(yScroll => {
      cy.wrap(yScroll).as('pageEndY');
    });

    cy.get('body').type('{home}');
    cy.window().its('scrollY').then(yScroll => {
      expect(yScroll).to.equal(0);
    });

    cy.get('body').type('{end}');
    cy.window().its('scrollY').then(yScroll => {
      cy.get('@pageEndY').should('equal', yScroll);
    });
  });

  it('should load more genes when scrolling', () => {
    cy.get('.table tr').should('have.length.above', 5);

    cy.get('.table').find('tr').its('length').then(value => {
      cy.scrollTo('bottom');
      cy.get('.table tr').should('have.length.above', value);
    });
  });
});

// describe('Autism gene profiles compare modal tests', () => {
//   const page = new AutismGeneProfilesTable();
//   const autismGeneProfilesBlock = new AutismGeneProfilesBlock();

//   before(() => {
//     autismGeneProfilesBlock.cleanup();
//   });

//   beforeEach(() => {
//     autismGeneProfilesBlock.navigateToHome();
//     autismGeneProfilesBlock.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
//   });

//   it.only('should select multiple genes and check whether the modal appears correctly', () => {
//     cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=**').as('tableRequest');

//     page.compareGenesModal.should('not.be.visible');
//     page.geneSearchInput.clear().type('MYT1L');
//     cy.wait('@tableRequest');
//     page.allTableRows.eq(0).click({ctrlKey: true});
//     page.compareGenesModal.should('be.visible');
//     page.compareGeneItems.should('have.length', 1);

//     page.allTableRows.eq(0).click({ctrlKey: true});
//     page.compareGenesModal.should('not.be.visible');

//     page.allTableRows.eq(0).click({ctrlKey: true});
//     page.compareGenesModal.should('be.visible');
//     page.compareGeneItems.should('have.length', 1);

//     page.geneSearchInput.clear().type('SPAST');
//     cy.wait('@tableRequest');
//     page.allTableRows.eq(0).click({ctrlKey: true});
//     page.compareGeneItems.should('have.length', 2);
//   });
// });

