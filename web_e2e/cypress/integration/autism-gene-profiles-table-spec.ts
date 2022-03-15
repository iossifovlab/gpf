import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
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

  it('should display sorting buttons', () => {
    page.allSortingButtons.should('be.visible');
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
    {geneSymbol: 'CHD8', expectedRow: 'CHD8✓✓✓✓✓11938331.5181787.0 (2.79)'},
    {geneSymbol: 'SHANK2', expectedRow: 'SHANK2✓✓✓243649175171.0 (0.4)1.0 (0.52)'},
    {geneSymbol: 'FLG', expectedRow: 'FLG✓1664018394.51.0 (0.4)'},
    {geneSymbol: 'CMIP', expectedRow: 'CMIP✓7558249469417467'},
    {geneSymbol: 'TBCD', expectedRow: 'TBCD✓6469111.513275.52221.0 (0.52)2.0 (1.05)'}
  ].forEach(data => {
    it(`should display correct gene data for ${data.geneSymbol}`, () => {
      page.geneSearchInput.type(data.geneSymbol);
      page.allTableRows.should('have.length', 1);

      page.allTableRows.eq(0).should('have.text', data.expectedRow);
    });
  });
});

describe('Autism gene profiles table column filtering modal tests', {scrollBehavior: false}, () => {
  const page = new AutismGeneProfilesTable();

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
    page.autismGeneSetColumnFilteringButton.click();
  });

  it('should open autism gene sets dropdown after clicking on the autism gene sets columns filtering button', () => {
    page.multipleSelectMenu.should('be.visible');
  });

  it('should open gene sets dropdown and display the check/uncheck all button', () => {
    page.multipleSelectMenuCheckUncheckAllButton.should('be.visible');
  });

  it('should open gene sets dropdown and display the search input box', () => {
    page.multipleSelectMenuSearch.should('be.visible');
  });

  it('should check/uncheck all gene sets column filtering options using the check/uncheck all button', () => {
    page.allMultipleSelectMenuCheckboxes.each(element => {
      cy.wrap(element).should('be.checked');
    });
    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.allMultipleSelectMenuCheckboxes.each(element => {
      cy.wrap(element).should('not.be.checked');
    });
    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.allMultipleSelectMenuCheckboxes.each(element => {
      cy.wrap(element).should('be.checked');
    });
  });

  it('should change the check/uncheck button text', () => {
    page.multipleSelectMenuCheckUncheckAllButton.should('have.text', 'Uncheck all');

    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.should('have.text', 'Check all');

    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.should('have.text', 'Uncheck all');
  });

  it('should filter gene sets dropdown options using the search', () => {
    page.allMultipleSelectMenuCheckboxes.should('have.length', 2);
    page.multipleSelectMenuSearch.type('iossifov');
    page.allMultipleSelectMenuCheckboxes.should('have.length', 1);
  });
});

describe('Autism gene profiles table row highlight tests', {scrollBehavior: false}, () => {
  const page = new AutismGeneProfilesTable();
  const oddHighlightColor = 'rgb(247, 247, 203)';
  const evenHighlightColor = 'rgb(255, 255, 214)';

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should highlight a row using control+click and change it\'s background color', () => {
    page.firstTableRow.should('not.have.class', 'row-highlight');

    page.firstTableRow.click('left', {ctrlKey: true});

    page.firstTableRow.should('have.class', 'row-highlight');
    page.firstTableRow.should('have.css', 'background-color').and('eq', oddHighlightColor);

    page.firstTableRow.click('left', {ctrlKey: true});
    page.firstTableRow.should('not.have.class', 'row-highlight');
    page.firstTableRow.should('not.have.property', 'background-color');
  });

  it('should highlight a several rows and check whether background color is different for odd and even rows', () => {
    page.allTableRows.eq(0).click('left', {ctrlKey: true});
    page.allTableRows.eq(1).click('left', {ctrlKey: true});
    page.allTableRows.eq(2).click('left', {ctrlKey: true});
    page.allTableRows.eq(3).click('left', {ctrlKey: true});
    page.allTableRows.eq(4).click('left', {ctrlKey: true});

    page.allTableRows.eq(0).should('have.css', 'background-color').and('eq', oddHighlightColor);
    page.allTableRows.eq(1).should('have.css', 'background-color').and('eq', evenHighlightColor);
    page.allTableRows.eq(2).should('have.css', 'background-color').and('eq', oddHighlightColor);
    page.allTableRows.eq(3).should('have.css', 'background-color').and('eq', evenHighlightColor);
    page.allTableRows.eq(4).should('have.css', 'background-color').and('eq', oddHighlightColor);
  });

  it('should highlight the first 3 rows and then press escape to remove all highlights', () => {
    page.allTableRows.eq(0).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(1).should('not.have.class', 'row-highlight');
    page.allTableRows.eq(2).should('not.have.class', 'row-highlight');

    page.allTableRows.eq(0).click('left', {ctrlKey: true});
    page.allTableRows.eq(1).click('left', {ctrlKey: true});
    page.allTableRows.eq(2).click('left', {ctrlKey: true});

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

  // it('should test statistic to genotype browser test', () => {
  //   page.loginAdmin();

  //   cy.intercept({
  //     method: 'POST',
  //     url: '/gpf/api/v3/query_state/save'
  //   }).as('query');
  //   page.geneSearchInput.type('CHD8');
  //   page.allTableRows.should('have.length', 1);
  //   cy.get('tr.ng-star-inserted > :nth-child(13)').click();
  //   cy.wrap('denovo_lgds').as('effectType');
  //   cy.wait('@query');
  //   cy.get('@query').then(req => {
  //     if (req !== null) {
  //       const genotypeBlockPage = new GenotypeBlockPage();
  //       cy.visit(Cypress.config().baseUrl + '/load-query/' + req.response.body.uuid);
  //       genotypeBlockPage.findCheckboxInComponentContainingText('.pedigree-selector-card', 'affected').parent().within(checkBoxes => {
  //         cy.wrap(checkBoxes).get('input').should('be.checked');
  //         cy.get('@effectType').then(effectType => {
  //           page.getStudyExpectedDataFromGenotype(effectType);
  //         });
  //       });
  //       page.getStudyActualDataFromGenotype();
  //       cy.get('@genotypeExpectedWrapper').then(expected => {
  //         cy.get('@genotypeActualWrapper').then(actual => {
  //           expect(expected).to.deep.equal(actual);
  //         });
  //       });
  //     }
  //   });
  // });

  // it('should sort genes by autism gene sets', () => {
  //   page.geneSearchInput.type('RAPGEF');
  //   page.allTableRows.should('have.length', 4);

  //   const dataArr = [[0, 0, 1], [0, 0, 0], [0, 0, 0], [1, 0, 0]];

  //   page.allSortingButtons.eq(0).click();
  //   dataArr.forEach((allRows, allRowsIndex) => {
  //     allRows.forEach((rowData, rowIndex) => {
  //       page.allTableRows.eq(allRowsIndex).within(row => {
  //         cy.wrap(row).get('td').eq(rowIndex+1).should('have.text', rowData === 1 ? '✓' : '');
  //       });
  //     });
  //   });

  //   dataArr.sort((a, b) => b[0] - a[0]);

  //   page.allSortingButtons.eq(0).click();
  //   dataArr.forEach((allRows, allRowsIndex) => {
  //     allRows.forEach((rowData, rowIndex) => {
  //       page.allTableRows.eq(allRowsIndex).within(row => {
  //         cy.wrap(row).get('td').eq(rowIndex+1).should('have.text', rowData === 1 ? '✓' : '');
  //       });
  //     });
  //   });
  // });

  // it('should sort genes by relevant gene sets', () => {
  //   page.geneSearchInput.type('RAPGEF');
  //   page.allTableRows.should('have.length', 4);

  //   page.clickSortButton('Relevant Gene Sets');
  //   page.allTableRows.should('have.length', 4);

  //   const dataArr = [
  //     [1, 0, 1, 1],
  //     [0, 0, 1, 1],
  //     [0, 0, 0, 1],
  //     [0, 0, 0, 1]
  //   ];

  //   dataArr.forEach((allRows, allRowsIndex) => {
  //     allRows.forEach((rowData, rowIndex) => {
  //       page.allTableRows.eq(allRowsIndex).within(row => {
  //         cy.wrap(row).get('td').eq(rowIndex + 3).should('have.text', rowData === 1 ? '✓' : '');
  //       });
  //     });
  //   });

  //   page.clickSortButton('Relevant Gene Sets');
  //   page.allTableRows.should('have.length', 4);

  //   dataArr.reverse();
  //   dataArr.forEach((allRows, allRowsIndex) => {
  //     allRows.forEach((rowData, rowIndex) => {
  //       page.allTableRows.eq(allRowsIndex).within(row => {
  //         cy.wrap(row).get('td').eq(rowIndex+3).should('have.text', rowData === 1 ? '✓' : '');
  //       });
  //     });
  //   });
  // });

  // it('should test autism scores', () => {
  //   page.geneSearchInput.type('CHD');
  //   page.allTableRows.should('have.length', 15);

  //   page.clickSortButton('SFARI_gene_score');

  //   const dataArr = [2, 1, null];
  //   dataArr.forEach((rowData, allRowsIndex) => {
  //     page.allTableRows.should('have.length', 15);
  //     page.allTableRows.eq(allRowsIndex).within(row => {
  //       cy.wrap(row).get('td').eq(7).should('have.text', rowData === null ? '' : rowData);
  //     });
  //   });

  //   dataArr.reverse();
  //   page.clickSortButton('SFARI_gene_score');

  //   dataArr.forEach((rowData, allRowsIndex) => {
  //     page.allTableRows.should('have.length', 15);
  //     page.allTableRows.eq(allRowsIndex).within(row => {
  //       cy.wrap(row).get('td').eq(7).should('have.text', rowData === null ? '' : rowData);
  //     });
  //   });
  // });

  // it('should compare protection scores', () => {
  //   page.geneSearchInput.type('RAPGEF');
  //   page.allTableRows.should('have.length', 4);

  //   [
  //     ['RVIS_rank', 2208.5, 449, 2187.5, 383],
  //     ['LGD_rank', 10012.5, 1838.5, 737, 299.5],
  //     ['pLI_rank', 3433, 374, 2574, 659],
  //     ['pRec_rank', 13429, 17823, 14843, 17507]
  //   ].forEach((dataArray, columnIndex) => {
  //     page.clickSortButton(dataArray[0]);
  //     const valuesArray = dataArray.splice(1);
  //     valuesArray.sort((a, b) => b - a);
  //     valuesArray.forEach((rowData, rowIndex) => {
  //       page.allTableRows.should('have.length', 4);
  //       page.allTableRows.eq(rowIndex).within(row => {
  //         cy.wrap(row).get('td').eq(8 + columnIndex).should('have.text', rowData);
  //       });
  //     });

  //     page.clickSortButton(dataArray[0]);
  //     valuesArray.sort((a, b) => a - b);
  //     valuesArray.forEach((rowData, rowIndex) => {
  //       page.allTableRows.should('have.length', 4);
  //       page.allTableRows.eq(rowIndex).within(row => {
  //         cy.wrap(row).get('td').eq(8 + columnIndex).should('have.text', rowData);
  //       });
  //     });
  //   });
  // });

  it('should show nothing found when search query dosent match', () => {
    page.nothingFound.should('not.be.visible');

    page.geneSearchInput.type('ewoqoqwekwoqkeowqkeowqkeoqwk');
    page.nothingFound.should('be.visible');
    page.nothingFound.should('have.text', 'Nothing found');

    page.geneSearchInput.clear();
    page.allTableRows.should('have.length.above', 1);
    page.nothingFound.should('not.be.visible');
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

