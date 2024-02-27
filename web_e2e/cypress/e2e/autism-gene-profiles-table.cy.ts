import { GeneProfilesTablePage } from 'cypress/elements/autism-gene-profiles-table-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles table tests', () => {
  const page = new GeneProfilesTablePage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.navigateToSidenavPage(sidenavPageLinks.geneProfiles);
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
  const page = new GeneProfilesTablePage();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome(false);
    page.navigateToSidenavPage(sidenavPageLinks.geneProfiles);
  });

  // refactor;
  // on test failure caused by a value change in the row,
  // it's hard to track in which specific column the change has occured
  [
    {geneSymbol: 'CHD8', expectedRow: 'CHD8✓✓✓✓✓11938331.5181787.0 (2.79)'},
    {geneSymbol: 'SHANK2', expectedRow: 'SHANK2✓✓✓143649175171.0 (0.4)1.0 (0.52)'},
    {geneSymbol: 'FLG', expectedRow: 'FLG✓1664018394.51.0 (0.4)'},
    {geneSymbol: 'CMIP', expectedRow: 'CMIP✓3558249469417467'},
    {geneSymbol: 'TBCD', expectedRow: 'TBCD✓6469111.513275.52222.0 (1.05)'}
  ].forEach(data => {
    it.only(`should display correct gene data for ${data.geneSymbol}`, () => {
      page.geneSearchInput.type(data.geneSymbol);
      page.allTableRows.should('have.length', 1);

      page.allTableRows.eq(0).should('have.text', data.expectedRow.replace(/✓/g, 'check_small'));
    });
  });
});

describe('Autism gene profiles table column filtering tests', {scrollBehavior: false}, () => {
  const page = new GeneProfilesTablePage();

  beforeEach(() => {
    page.navigateToHome(false);
    page.navigateToSidenavPage(sidenavPageLinks.geneProfiles);
  });

  it('should open autism gene sets dropdown after clicking on the autism gene sets columns filtering button', () => {
    page.autismGeneSetColumnFilteringButton.click();
    page.multipleSelectMenu.should('be.visible');
    page.multipleSelectMenuCheckUncheckAllButton.should('be.visible');
    page.multipleSelectMenuSearch.should('be.visible');
  });

  it('should check/uncheck all gene sets column filtering options using the check/uncheck all button', () => {
    page.autismGeneSetColumnFilteringButton.click();
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
    page.autismGeneSetColumnFilteringButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.should('have.text', 'Uncheck all');

    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.should('have.text', 'Check all');

    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.should('have.text', 'Uncheck all');
  });


  it('should test the check/uncheck button', () => {
    page.autismGeneSetColumnFilteringButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.click();

    page.columnHeader('Autism Gene Sets').should('not.exist');
    page.columnHeader('autism candidates from Iossifov PNAS 2015').should('not.exist');
    page.columnHeader('autism candidates from Sanders Neuron 2015').should('not.exist');
    cy.get('body').click(0, 0);

    page.categoryFilterButton.click();
    page.multipleSelectMenuCheckboxText('Autism Gene Sets').should('not.be.checked');
    page.multipleSelectMenuCheckboxText('Autism Gene Sets').click();
    cy.get('body').click(0, 0);

    page.autismGeneSetColumnFilteringButton.click();
    page.columnHeader('Autism Gene Sets').should('be.visible');
    page.columnHeader('autism candidates from Iossifov PNAS 2015').should('be.visible');
    page.columnHeader('autism candidates from Sanders Neuron 2015').should('be.visible');
  });

  it('should filter gene sets dropdown options using the search', () => {
    page.autismGeneSetColumnFilteringButton.click();
    page.allMultipleSelectMenuCheckboxes.should('have.length', 2);
    page.multipleSelectMenuSearch.type('iossifov');
    page.allMultipleSelectMenuCheckboxes.should('have.length', 1);
  });

  it('should uncheck gene set from autism gene sets dropdown and check table header', () => {
    page.autismGeneSetColumnFilteringButton.click();
    page.multipleSelectMenuCheckboxText('autism candidates from Sanders Neuron 2015').click();
    page.columnHeader('autism candidates from Sanders Neuron 2015').should('not.exist');

    page.multipleSelectMenuCheckboxText('autism candidates from Sanders Neuron 2015').click();
    page.columnHeader('autism candidates from Sanders Neuron 2015').should('be.visible');
  });

  it('should uncheck iossifov_2014 and check table header', () => {
    page.categoryFilterButton.click();
    page.multipleSelectMenuCheckboxText('iossifov_2014').click();
    page.columnHeader('affected').should('not.exist');
    page.columnHeader('unaffected').should('not.exist');
    page.columnHeader('LGDs').should('not.exist');
    page.columnHeader('missense').should('not.exist');
    page.columnHeader('intron').should('not.exist');
    cy.get('.header-cell').should('have.length', 16);

    page.multipleSelectMenuCheckboxText('iossifov_2014').click();
    page.columnHeader('affected').should('be.visible');
    page.columnHeader('unaffected').should('be.visible');
    page.columnHeader('LGDs').should('be.visible');
    page.columnHeader('missense').should('be.visible');
    page.columnHeader('intron').should('be.visible');
    cy.get('.header-cell').should('have.length', 25);
  });

  it('should drag and drop gene set and check table header', () => {
    page.categoryFilterButton.click();

    page.allMultipleSelectMenuOptions.first().should('have.text', 'Autism Gene Sets');
    page.allColumnHeaders.eq(1).should('have.text', 'Autism Gene Sets');
    page.allColumnHeaders.eq(2).should('have.text', 'autism candidates from Iossifov PNAS 2015');
    page.allColumnHeaders.eq(3).should('have.text', 'autism candidates from Sanders Neuron 2015');

    page.multipleSelectMenuCheckboxText('Autism Gene Sets')
      .trigger('mousedown', {
        button: 0,
        pageX: 0,
        pageY: 0,
        force: true
      })
      .trigger('mousemove', {
        force: true
      })
      .trigger('mousemove', {
        button: 0,
        pageX: 430,
        pageY: 230,
        force: true
      })
      .trigger('mouseup', {
        button: 0,
        force: true,
      });

    page.allMultipleSelectMenuOptions.first().should('have.text', 'Relevant Gene Sets');
    page.allMultipleSelectMenuOptions.eq(1).should('have.text', 'Autism Gene Sets');

    page.allColumnHeaders.eq(1).should('have.text', 'Relevant Gene Sets');
    page.allColumnHeaders.eq(2).should('have.text', 'CHD8 target genes');
    page.allColumnHeaders.eq(3).should('have.text', 'chromatin modifiers');
    page.allColumnHeaders.eq(4).should('have.text', 'essential genes');
    page.allColumnHeaders.eq(5).should('have.text', 'FMRP Darnell');

    page.allColumnHeaders.eq(6).should('have.text', 'Autism Gene Sets');
    page.allColumnHeaders.eq(7).should('have.text', 'autism candidates from Iossifov PNAS 2015');
    page.allColumnHeaders.eq(8).should('have.text', 'autism candidates from Sanders Neuron 2015');
  });
});

describe('Autism gene profiles gene comparison tests', {scrollBehavior: false}, () => {
  const page = new GeneProfilesTablePage();
  const oddHighlightColor = 'rgb(247, 247, 203)';
  const evenHighlightColor = 'rgb(255, 255, 214)';

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome(false);
    page.navigateToSidenavPage(sidenavPageLinks.geneProfiles);
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

  it('should select multiple genes and check whether the modal appears correctly', () => {
    page.compareGenesModal.should('not.exist');

    page.allTableRows.eq(0).click('left', {ctrlKey: true});
    page.allTableRows.eq(1).click('left', {ctrlKey: true});
    page.allTableRows.eq(2).click('left', {ctrlKey: true});
    page.compareGenesModal.should('be.visible');
    page.compareGeneItems.should('have.length', 3);

    page.allTableRows.eq(0).click('left', {ctrlKey: true});
    page.allTableRows.eq(1).click('left', {ctrlKey: true});
    page.allTableRows.eq(2).click('left', {ctrlKey: true});
    page.compareGenesModal.should('not.exist');
  });

  it('should select multiple genes and remove them from modal', () => {
    page.compareGenesModal.should('not.exist');

    page.allTableRows.eq(0).click('left', {ctrlKey: true});
    page.allTableRows.eq(1).click('left', {ctrlKey: true});
    page.allTableRows.eq(2).click('left', {ctrlKey: true});
    page.compareGenesModal.should('be.visible');
    page.compareGeneItems.should('have.length', 3);

    page.findButtonInComponentContainingText('.compare-genes-close', '×').click();
    page.allTableRows.eq(0).should('not.have.class', 'row-highlight');
    page.compareGeneItems.should('have.length', 2);

    page.findButtonInComponentContainingText('.compare-genes-close', '×').click();
    page.allTableRows.eq(1).should('not.have.class', 'row-highlight');
    page.compareGeneItems.should('have.length', 1);

    page.findButtonInComponentContainingText('.compare-genes-close', '×').click();
    page.allTableRows.eq(2).should('not.have.class', 'row-highlight');
    page.compareGenesModal.should('not.exist');
  });
});

describe('Autism gene profiles table functionality tests', () => {
  const page = new GeneProfilesTablePage();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome(false);
    page.navigateToSidenavPage(sidenavPageLinks.geneProfiles);
  });

  it('should sort genes by autism gene sets', () => {
    page.geneSearchInput.type('RAPGEF');
    page.allTableRows.should('have.length', 4);

    page.categoryFilterButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.multipleSelectMenuCheckboxText('Autism Gene Sets').click();
    page.categoryFilterButton.click();

    page.columnHeader('Autism Gene Sets').click();
    cy.wait(200); // wait old content to be replaced


    page.allTableRows.eq(0).invoke('text').then(text => expect(text.split('✓').length-1).equal(0));
    page.allTableRows.eq(1).invoke('text').then(text => expect(text.split('✓').length-1).equal(0));
    page.allTableRows.eq(2).invoke('text').then(text => expect(text.split('✓').length-1).equal(0));
    page.allTableRows.eq(3).within(el => {
      cy.wrap(el).get('span.check').invoke('text').then(text => {
        expect(text).to.deep.eq('check_small');
      });
    });

    page.columnHeader('Autism Gene Sets').click();
    page.allTableRows.should('have.length', 4);
    cy.wait(200);
    page.allTableRows.eq(0).within(el => {
      cy.wrap(el).get('span.check').invoke('text').then(text => {
        expect(text).to.deep.eq('check_small');
      });
    });
    page.allTableRows.eq(1).invoke('text').then(text => expect(text.split('✓').length-1).equal(0));
    page.allTableRows.eq(2).invoke('text').then(text => expect(text.split('✓').length-1).equal(0));
    page.allTableRows.eq(3).invoke('text').then(text => expect(text.split('✓').length-1).equal(0));
  });

  it('should sort genes by relevant gene sets', () => {
    page.geneSearchInput.type('SENP');
    page.allTableRows.should('have.length', 6);

    page.categoryFilterButton.click();
    page.multipleSelectMenuCheckUncheckAllButton.click();
    page.multipleSelectMenuCheckboxText('Relevant Gene Sets').click();
    page.categoryFilterButton.click();

    page.columnHeader('Relevant Gene Sets').click();
    cy.wait(200);
    page.allTableRows.eq(0).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(2);
      });
    });
    page.allTableRows.eq(1).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(2).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(3).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(4).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(5).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });


    page.columnHeader('Relevant Gene Sets').click();
    cy.wait(200);
    page.allTableRows.eq(0).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(1).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(2).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(3).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(4).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(1);
      });
    });
    page.allTableRows.eq(5).within(el => {
      cy.wrap(el).get('span.check').then(text => {
        expect(text).to.have.length(2);
      });
    });
  });

  it('should test autism scores', () => {
    page.geneSearchInput.type('CHD');
    page.allTableRows.should('have.length', 15);

    page.clickSortButton('SFARI gene score');
    cy.wait(750);

    const dataArr = [3, 1, 1, 1, 1];
    dataArr.forEach((rowData, allRowsIndex) => {
      page.allTableRows.should('have.length', 15);
      page.allTableRows.eq(allRowsIndex).within(row => {
        cy.wrap(row).get('div').eq(7).should('have.text', rowData === null ? '' : rowData);
      });
    });

    dataArr.reverse();
    page.clickSortButton('SFARI gene score');
    cy.wait(750);

    dataArr.forEach((rowData, allRowsIndex) => {
      page.allTableRows.should('have.length', 15);
      page.allTableRows.eq(allRowsIndex).within(row => {
        cy.wrap(row).get('div').eq(7).should('have.text', rowData === null ? '' : rowData);
      });
    });
  });

  // Sort results change slowly and cypress gets the old result instead of the new
  // should be refactored in playwright to use data.forEach(it()) structure
  // and not have loop inside the test
  it.skip('should compare protection scores', () => {
    page.geneSearchInput.type('RAPGEF');
    page.allTableRows.should('have.length', 4);

    [
      ['RVIS_rank', 2208.5, 449, 2187.5, 383],
      ['LGD_rank', 10012.5, 1838.5, 737, 299.5],
      ['pLI_rank', 3433, 374, 2574, 659],
      ['pRec_rank', 13429, 17823, 14843, 17507]
    ].forEach((dataArray, columnIndex) => {
      page.clickSortButton(dataArray[0] as string);
      const valuesArray = dataArray.splice(1);
      valuesArray.sort((a: number, b: number) => b - a);
      valuesArray.forEach((rowData, rowIndex) => {
        page.allTableRows.should('have.length', 4);
        page.allTableRows.eq(rowIndex).within(row => {
          cy.wrap(row).get('div').eq(8 + columnIndex).should('have.text', rowData);
        });
      });

      page.clickSortButton(dataArray[0] as string);
      valuesArray.sort((a: number, b: number) => a - b);
      valuesArray.forEach((rowData, rowIndex) => {
        page.allTableRows.should('have.length', 4);
        page.allTableRows.eq(rowIndex).within(row => {
          cy.wrap(row).get('div').eq(8 + columnIndex).should('have.text', rowData);
        });
      });
    });
  });

  it('should show nothing found when search query doesn\'t match', () => {
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
    cy.wait(1000);
    cy.window().its('scrollY').then(yScroll => {
      cy.wrap(yScroll).as('pageEndY');
    });

    cy.get('body').type('{home}');
    cy.wait(1000);
    cy.window().its('scrollY').then(yScroll => {
      expect(yScroll).to.equal(0);
    });

    cy.get('body').type('{end}');
    cy.wait(1000);
    cy.window().its('scrollY').then(yScroll => {
      cy.get('@pageEndY').should('equal', yScroll);
    });
  });

  it('should test statistic to genotype browser test', () => {
    page.loginAdmin(true);

    cy.intercept({
      method: 'POST',
      url: '/gpf/api/v3/query_state/save'
    }).as('query');
    page.geneSearchInput.type('CHD8');
    page.allTableRows.should('have.length', 1);

    cy.window().then(win => {
      cy.stub(win, 'open');
    });
    page.allTableCells.eq(12).click();
    cy.wrap('denovo_lgds').as('effectType');
    cy.wait('@query');
    cy.get('@query').then(req => {
      if (req !== null) {
        const genotypeBlockPage = new GenotypeBlockPage();
        cy.visit(Cypress.config().baseUrl + '/load-query/' + req['response'].body.uuid);
        genotypeBlockPage.findCheckboxInComponentContainingText('.pedigree-selector-card', 'affected')
          .parent().within(checkBoxes => {
          // add waitForPageToLoad logic after visit...
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

    page.logout();
  });
});
