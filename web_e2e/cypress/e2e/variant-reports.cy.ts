import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { VariantReportsPage } from 'cypress/elements/variant-reports-page';

const tags: string[] = [
  'tag_nuclear_family',
  'tag_quad_family',
  'tag_trio_family',
  'tag_simplex_family',
  'tag_multiplex_family',
  'tag_control_family',
  'tag_affected_dad_family',
  'tag_affected_mom_family',
  'tag_affected_prb_family',
  'tag_affected_sib_family',
  'tag_unaffected_dad_family',
  'tag_unaffected_mom_family',
  'tag_unaffected_prb_family',
  'tag_unaffected_sib_family',
  'tag_male_prb_family',
  'tag_female_prb_family',
  'tag_missing_mom_family',
  'tag_missing_dad_family'
]
describe('Variant reports tests', () => {
  const page = new VariantReportsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
  });

  it('should always display "total number of families" and download all button', () => {
    page.familiesByNumberTab.click();
    page.totalNumberOfFamilies.should('be.visible');
    page.downloadAllLink.should('be.visible');

    page.familiesByPedigreeTab.click();
    page.totalNumberOfFamilies.should('be.visible');
    page.downloadAllLink.should('be.visible');

    page.deNovoVariantsTab.click();
    page.totalNumberOfFamilies.should('be.visible');
    page.downloadAllLink.should('be.visible');
  });

  it('should display the correct elements in the families by number tab', () => {
    page.familiesByNumberTab.click();
    page.familiesByNumberSelect.should('be.visible');
    page.familiesByNumber.should('be.visible');

    page.deNovoVariantsTab.click();
    page.familiesByNumberSelect.should('not.be.visible');
    page.familiesByNumber.should('not.be.visible');
  });

  it('should display the correct elements in the families by pedigree tab', () => {
    page.familiesByPedigreeTab.click();
    page.familiesByPedigreeSelect.should('be.visible');
    page.denovoTagSelector.should('be.visible');
    page.familiesByPedigreeDownloadButton.should('be.visible');
    page.familiesByPedigree.should('be.visible')

    page.deNovoVariantsTab.click();
    page.familiesByPedigreeSelect.should('not.be.visible');
    page.denovoTagSelector.should('not.be.visible');
    page.familiesByPedigreeDownloadButton.should('not.be.visible');
    page.familiesByPedigree.should('not.be.visible')
  });

  it('should display the correct elements in the de novo variants tab', () => {
    page.deNovoVariantsTab.click();
    page.denovoVariantsSelect.should('be.visible');
    page.denovoLegend.should('be.visible');
    page.denovoVariants.should('be.visible');

    page.familiesByNumberTab.click();
    page.denovoVariantsSelect.should('not.be.visible');
    page.denovoLegend.should('not.be.visible');
    page.denovoVariants.should('not.be.visible');
  });

  [
    {option: 'Affected Status', legendElements: ['affected', 'unaffected']},
    {option: 'Role', legendElements: ['mom', 'dad', 'proband', 'sibling']},
    {option: 'Phenotype', legendElements: ['autism', 'unaffected']}
  ].forEach(data => {
    it('should check content of the legend for ' + data.option + ' option in the families by pedigree tab', () => {
      page.familiesByPedigreeTab.click();
      page.pedigreeLegendButton.should('be.visible');
      page.pedigreeLegendDropdown.should('not.exist');
      page.familiesByPedigreeSelect.select(data.option);
      page.familiesByPedigreeSelect.find(':selected').contains(data.option);

      page.pedigreeLegendButton.click();
      page.pedigreeLegendDropdown.should('be.visible');

      page.pedigreeLegendDropdownElements.should('have.length', data.legendElements.length);

      data.legendElements.forEach(e => {
        page.pedigreeLegendDropdown.should('contain', e);
      })

      page.pedigreeLegendButton.click();
      page.pedigreeLegendDropdown.should('not.exist');
    })
  })

  it('should check content of the select in the families by pedigree tab', () => {
    page.familiesByPedigreeTab.click();
    page.familiesByPedigreeSelectOptions.then(options => {
      const actual: string[] = options.toArray().map(o => o.innerText);
      expect(actual).to.deep.eq(['Affected Status', 'Role', 'Phenotype']);
    })
  })

  it('should open, close and check content for selecting tags', () => {
    page.familiesByPedigreeTab.click();
    page.denovoTagSelectorDropdown.should('have.text', 'Select tags');
    page.denovoTagSelectorContent.should('be.hidden');

    page.denovoTagSelectorDropdown.click();
    page.denovoTagSelectorContent.should('not.be.hidden');

    // page.denovoTagSelectorDropdown.click();
    page.denovoTagSelectorDropdown.click(30, 30);
    page.denovoTagSelectorContent.should('be.hidden');

    page.denovoTagSelectorDropdown.click();
    page.denovoTagSelectorSearch.should('be.visible');
    page.denovoTagSelectorOptions.should('be.visible');
    page.denovoTagSelectorOptions.then(options => {
      const actual: string[] = options.toArray().map(o => o.innerText);
      expect(actual).to.deep.eq(tags);
    })
  });

  tags.forEach(tag => {
    it('should select and unselect tags', () => {
      page.familiesByPedigreeTab.click();

      //open the content, check an item
      page.denovoTagSelectorDropdown.click();
      page.denovoTagSelectorOptionsInput(tag).check({force: true});
      page.denovoTagSelectorOptions.find('input[aria-label="'+tag+'"]').should('be.checked');
      page.denovoTagSelectorSelectedOptions.contains(tag);

      // closing the content without unchecking
      // page.denovoTagSelectorDropdown.click();
      page.denovoTagSelectorDropdown.click(30, 30);
      page.denovoTagSelectorContent.should('be.hidden');
      page.denovoTagSelectorSelectedOptions.contains(tag);

      //open the content, check an item, delete the item
      page.denovoTagSelectorDropdown.click();
      page.denovoTagSelectorOptionsInput(tag).check({force: true});
      page.denovoTagSelectorOptions.find('input[aria-label="'+tag+'"]').should('be.checked');
      page.denovoTagSelectorSelectedOptionBtn.click();
      page.denovoTagSelectorSelectedOptions.should('not.contain', tag);
      page.denovoTagSelectorOptions.find('input[aria-label="'+tag+'"]').should('not.be.checked');
      page.denovoTagSelectorContent.should('be.hidden');

      //open the content check and uncheck
      page.denovoTagSelectorDropdown.click();
      page.denovoTagSelectorOptionsInput(tag).check({force: true});
      page.denovoTagSelectorOptions.find('input[aria-label="'+tag+'"]').should('be.checked');
      page.denovoTagSelectorSelectedOptions.contains(tag);

      page.denovoTagSelectorOptionsInput(tag).uncheck({force: true});
      page.denovoTagSelectorOptions.find('input[aria-label="'+tag+'"]').should('not.be.checked');
      page.denovoTagSelectorSelectedOptions.should('not.contain', tag);

      //close
      page.denovoTagSelectorDropdown.click();
    })
  });

  [
    {tag: 'tag_nuclear_family', expectedPredigrees: 8},
    {tag: 'tag_quad_family', expectedPredigrees: 4},
    {tag: 'tag_trio_family', expectedPredigrees: 4},
    {tag: 'tag_simplex_family', expectedPredigrees: 6},
    {tag: 'tag_multiplex_family', expectedPredigrees: 0},
    {tag: 'tag_control_family', expectedPredigrees: 2},
    {tag: 'tag_affected_dad_family', expectedPredigrees: 0},
    {tag: 'tag_affected_mom_family', expectedPredigrees: 0},
    {tag: 'tag_affected_prb_family', expectedPredigrees: 6},
    {tag: 'tag_affected_sib_family', expectedPredigrees: 0},
    {tag: 'tag_unaffected_dad_family', expectedPredigrees: 8},
    {tag: 'tag_unaffected_mom_family', expectedPredigrees: 8},
    {tag: 'tag_unaffected_prb_family', expectedPredigrees: 0},
    {tag: 'tag_unaffected_sib_family', expectedPredigrees: 6},
    {tag: 'tag_male_prb_family', expectedPredigrees: 3},
    {tag: 'tag_female_prb_family', expectedPredigrees: 3},
    {tag: 'tag_missing_mom_family', expectedPredigrees: 0},
    {tag: 'tag_missing_dad_family', expectedPredigrees: 0}
  ].forEach(element => {
    it('should select a single tag and check number of pedigree charts', () => {
      page.familiesByPedigreeTab.click();
      page.denovoTagSelectorDropdown.click();
      page.denovoTagSelectorOptionsInput(element.tag).check({force: true});
      page.pedigreeCells.should('have.length', element.expectedPredigrees);
    })
  });


  it('should search tags', () => {
    page.familiesByPedigreeTab.click();
    page.denovoTagSelectorDropdown.click();
    const serchingValues: string[] = ['a', 'ro', 'lex', 'as'];

    for (let i = 0; i < serchingValues.length; i++) {
      page.denovoTagSelectorSearchInput.type(serchingValues[i]);
      const filtered: string[] = tags.filter(tag => tag.includes(serchingValues[i]));
      if (filtered.length === 0) {
        page.denovoTagSelectorSearchInputNothingFound.should('exist');
      } else {
        page.denovoTagSelectorOptions.then(options => {
          const actual: string[] = options.toArray().map(o => o.innerText);
          expect(actual).to.deep.eq(filtered);
        })
      }
      page.denovoTagSelectorSearchInput.clear();
    }
  });
});

describe('Variant reports Iossifov count tests', () => {
  const page = new VariantReportsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
  });

  [
    {rowIndex: 0, roleId: 'mom', expectedCounts: ['0', '2516', '2516']},
    {rowIndex: 1, roleId: 'dad', expectedCounts: ['2516', '0', '2516']},
    {rowIndex: 2, roleId: 'proband', expectedCounts: ['2166', '341', '2507']},
    {rowIndex: 3, roleId: 'sibling', expectedCounts: ['899', '1011', '1910']}
  ].forEach(data => {
    it('should display the correct numbers in families by numbers of role - "' + data.roleId + '"', () => {
      page.familiesByNumberSelect.select('Role');

      page.allFamiliesByNumberHeaderCells.eq(data.rowIndex).should('have.text', data.roleId);

      page.allFamiliesByNumberDataCells.as('tds');
      for (let i = 0; i < data.expectedCounts.length; i++) {
        cy.get('@tds').eq((data.rowIndex * 3) + i).should('have.text', data.expectedCounts[i])
      }
    });
  });

  it('should display the correct numbers in families by pedigree of affected status', () => {
    const expectedValues: string[] = ['877', '789', '500', '128', '107', '106', '6', '3'];
    page.familiesByNumberTab.click();
    page.familiesByPedigreeDivs.each((ele, i) => {
      expect(ele.text()).to.eq(expectedValues[i]);
    })
  });

  [
    {effectType: 'LGDs', expectedCounts: ['393, 0.157(366, 15%)', '180, 0.094(169, 9%)']},
    {effectType: 'UTRs', expectedCounts: ['244, 0.097(237, 9%)', '154, 0.081(144, 8%)']},
    {effectType: 'Missense', expectedCounts: ['1680, 0.67(1185, 47%)', '1149, 0.602(843, 44%)']},
    {effectType: 'Intron', expectedCounts: ['821, 0.327(671, 27%)', '558, 0.292(464, 24%)']}
  ].forEach(data => {
    it('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" role table', () => {
      page.deNovoVariantsTab.click();
      page.denovoVariantsSelect.select('Role');
      page.findDenovoVariantsCountsByRowName(data.effectType).each((ele, i) => {
        expect(ele.text()).to.eq(data.expectedCounts[i]);
      });
    });
  });

  [
    {effectType: 'LGDs', expectedCounts: ['393, 0.157(366, 15%)', '180, 0.094(169, 9%)']},
    {effectType: 'UTRs', expectedCounts: ['244, 0.097(237, 9%)', '154, 0.081(144, 8%)']},
    {effectType: 'Missense', expectedCounts: ['1680, 0.67(1185, 47%)', '1149, 0.602(843, 44%)']},
    {effectType: 'Intron', expectedCounts: ['821, 0.327(671, 27%)', '558, 0.292(464, 24%)']}
  ].forEach(data => {
    it('should display the correct numbers for ' + data.effectType +
        ' effectType in the "Denovo variants of:" status table', () => {
      page.deNovoVariantsTab.click();
      page.denovoVariantsSelect.select('Affected Status');
      page.findDenovoVariantsCountsByRowName(data.effectType).each((ele, i) => {
        expect(ele.text()).to.eq(data.expectedCounts[i]);
      });
    });
  });
});

describe.skip('Variant reports visual tests', () => {
  const page = new VariantReportsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
  });

  it('should compare family by number table data', () => {
    page.familiesByNumberTab.click();

    cy.get('#families-by-number-div').matchImageSnapshot('iossifov-family-table-status');

    page.familiesByNumberSelect.select('Role');
    cy.get('#families-by-number-div').matchImageSnapshot('iossifov-family-table-role');

    page.familiesByNumberSelect.select('Phenotype');
    cy.get('#families-by-number-div').matchImageSnapshot('iossifov-family-table-phenotype');
  });

  it('should compare families by pedigree table data', () => {
    page.familiesByPedigreeTab.click();

    cy.get('#families-by-pedigree-div').scrollIntoView().matchImageSnapshot('iossifov-pedigree-table-status');

    cy.get('.col-sm-3 > .select-wrapper > .form-control').select('Role');
    page.familiesByPedigreeDivs.should('have.length', 8);
    cy.get('#families-by-pedigree-div').scrollIntoView().matchImageSnapshot('iossifov-pedigree-table-role');

    cy.get('.col-sm-3 > .select-wrapper > .form-control').select('Phenotype');
    page.familiesByPedigreeDivs.should('have.length', 8);
    cy.get('#families-by-pedigree-div').scrollIntoView().matchImageSnapshot('iossifov-pedigree-table-phenotype');
  });

  it('should compare de novo variants table data', () => {
    page.deNovoVariantsTab.click();

    cy.get('#denovo-variants-div').scrollIntoView().matchImageSnapshot('iossifov-denovo-table-status');

    page.denovoVariantsSelect.select('Role');
    cy.get('#denovo-variants-div').scrollIntoView().matchImageSnapshot('iossifov-denovo-table-role');

    page.denovoVariantsSelect.select('Phenotype');
    cy.get('#denovo-variants-div').scrollIntoView().matchImageSnapshot('iossifov-denovo-table-phenotype');
  });
});