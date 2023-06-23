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
];

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
    cy.deleteDownloadsFolder();
  });

  it('should display the correct elements in the families by number tab', () => {
    page.familiesByNumberTab.click();
    page.downloadAllFamilies.should('be.visible');
    page.familiesByNumberSelect.should('be.visible');
    page.familiesByNumber.should('be.visible');

    page.deNovoVariantsTab.click();
    page.downloadAllFamilies.should('not.be.visible');
    page.familiesByNumberSelect.should('not.be.visible');
    page.familiesByNumber.should('not.be.visible');
  });

  it('should display the correct elements in the families by pedigree tab', () => {
    page.familiesByPedigreeTab.click();
    page.familiesByPedigreeSelect.should('be.visible');
    page.familiesByPedigreeDownloadButton.should('be.visible');
    page.familiesByPedigreeTable.should('be.visible');
    page.selectedTagsHeader.should('not.exist');

    page.deNovoVariantsTab.click();
    page.familiesByPedigreeSelect.should('not.be.visible');
    page.familiesByPedigreeDownloadButton.should('not.be.visible');
    page.familiesByPedigreeTable.should('not.be.visible');
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
      page.dropdown.select(data.option);

      page.pedigreeLegendButton.click();
      page.pedigreeLegendDropdown.should('be.visible');

      page.pedigreeLegendDropdownElements.should('have.length', data.legendElements.length);

      data.legendElements.forEach(e => {
        page.pedigreeLegendDropdown.should('contain', e);
      });

      page.pedigreeLegendButton.click();
      page.pedigreeLegendDropdown.should('not.exist');
    });
  });

  it('should check content of the select in the families by pedigree tab', () => {
    page.familiesByPedigreeTab.click();
    page.familiesByPedigreeSelectOptions.then(options => {
      const actual: string[] = options.toArray().map(o => o.innerText);
      expect(actual).to.deep.eq(['Affected Status', 'Role', 'Phenotype']);
    });
  });

  it('should open, close and check content for selecting tags', () => {
    page.familiesByPedigreeTab.click();
    page.openPedigreeTagsModal.should('have.text', 'Select tags');
    page.pedigreeTagsModal.should('not.exist');

    page.openPedigreeTagsModal.click();
    page.pedigreeTagsModal.should('be.visible');

    cy.get('body').click(0, 0);
    page.pedigreeTagsModal.should('not.exist');

    page.openPedigreeTagsModal.click();
    page.pedigreeTagsModalSearch.should('be.visible');
    page.pedigreeTagsModalUncheckAll.should('be.visible');
    page.pedigreeTagsModalTags.should('be.visible');
    page.pedigreeTagsModalTags.find('label').then(options => {
      const actual: string[] = options.toArray().map(o => o.innerText);
      expect(actual).to.deep.eq(tags);
    });
  });

  tags.forEach(tag => {
    it('should select and unselect each tag', () => {
      page.familiesByPedigreeTab.click();

      //open modal, check an item
      page.openPedigreeTagsModal.click();
      page.findTag(tag).click();
      page.findTagCheckbox(tag).should('be.checked');
      page.selectedTagsHeader.should('be.visible');
      page.selectedTagsHeader.contains(tag);

      // closing modal without unchecking
      cy.get('body').click(0, 0);
      page.selectedTagsHeader.contains(tag);

      //open modal and uncheck item
      page.openPedigreeTagsModal.click();
      page.findTag(tag).click();
      page.selectedTagsHeader.should('not.exist');
      page.findTagCheckbox(tag).should('not.be.checked');
    });
  });

  ['n', 'ro', 'lex'].forEach(searchValue =>
    it(`should search and find tags with ${searchValue}`, () => {
      page.familiesByPedigreeTab.click();
      page.openPedigreeTagsModal.click();

      page.pedigreeTagsModalSearch.type(searchValue);
      tags.forEach(tag => {
        if (tag.includes(searchValue)) {
          page.findTagCheckbox(tag).should('be.enabled');
        } else {
          page.findTagCheckbox(tag).should('be.disabled');
        }
      });
      page.pedigreeTagsModalSearch.clear();
    })
  );

  ['cot', 'riof', 'tsf', 'as'].forEach(searchValue =>
    it(`should show nothing found when searching tags with ${searchValue}`, () => {
      page.familiesByPedigreeTab.click();
      page.openPedigreeTagsModal.click();

      page.pedigreeTagsModalSearch.type(searchValue);
      tags.forEach(tag => {
        page.findTagCheckbox(tag).should('be.disabled');
      });
    })
  );

  [
    {tag: tags[0], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106', '6', '3']},
    {tag: tags[1], expectedPedigreeCounts: ['877', '789', '128', '107']},
    {tag: tags[2], expectedPedigreeCounts: ['500', '106', '6', '3']},
    {tag: tags[3], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106']},
    {tag: tags[5], expectedPedigreeCounts: ['6', '3']},
    {tag: tags[8], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106']},
    {tag: tags[10], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106', '6', '3']},
    {tag: tags[11], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106', '6', '3']},
    {tag: tags[13], expectedPedigreeCounts: ['877', '789', '128', '107', '6', '3']},
    {tag: tags[14], expectedPedigreeCounts: ['877', '789', '500']},
    {tag: tags[15], expectedPedigreeCounts: ['128', '107', '106']}
  ].forEach(data => {
    it(`should select ${data.tag} and check pedigree charts`, () => {
      page.familiesByPedigreeTab.click();
      page.openPedigreeTagsModal.click();
      page.findTag(data.tag).click();
      cy.get('body').click(0, 0);
      page.pedigreeCells.should('have.length', data.expectedPedigreeCounts.length);
      page.pedigreeCells.each((cell, i) => {
        expect(cell).to.have.text(data.expectedPedigreeCounts[i]);
      });
    });
  });

  [
    {tag: tags[4], expectedPedigreeCounts: []},
    {tag: tags[6], expectedPedigreeCounts: []},
    {tag: tags[7], expectedPedigreeCounts: []},
    {tag: tags[9], expectedPedigreeCounts: []},
    {tag: tags[12], expectedPedigreeCounts: []},
    {tag: tags[16], expectedPedigreeCounts: []},
    {tag: tags[17], expectedPedigreeCounts: []}
  ].forEach(data => {
    it(`should select ${data.tag} and check if nothing found is displayed`, () => {
      page.familiesByPedigreeTab.click();
      page.openPedigreeTagsModal.click();
      page.findTag(data.tag).click();
      cy.get('body').click(0, 0);
      page.pedigreesNothingFound.should('exist');
    });
  });

  it('should test uncheck all button in tags modal', () => {
    page.familiesByPedigreeTab.click();
    page.openPedigreeTagsModal.click();
    tags.forEach(tag => {
      page.findTag(tag).click();
      page.selectedTagsHeader.contains(tag);
    });
    page.pedigreeTagsModalUncheckAll.click();
    tags.forEach(tag => {
      page.findTagCheckbox(tag).should('not.be.checked');
      page.selectedTagsHeader.should('not.exist');
    });
  });

  [
    {selectedTags: [tags[2], tags[3]], expectedPedigreeCounts: ['500', '106']},
    {selectedTags: [tags[0], tags[3], tags[15]], expectedPedigreeCounts: ['128', '107', '106']},
    {selectedTags: [tags[3], tags[8], tags[13], tags[14]], expectedPedigreeCounts: ['877', '789']}
  ].forEach(data => {
    it('should select a multiple tags and check pedigree charts', () => {
      page.familiesByPedigreeTab.click();
      page.openPedigreeTagsModal.click();
      data.selectedTags.forEach(tag => {
        page.findTag(tag).click();
        page.selectedTagsHeader.contains(tag);
      });
      cy.get('body').click(0, 0);

      page.pedigreeCells.should('have.length', data.expectedPedigreeCounts.length);
      page.pedigreeCells.each((cell, i) => {
        expect(cell).to.have.text(data.expectedPedigreeCounts[i]);
      });

      page.openPedigreeTagsModal.click();
      page.pedigreeTagsModalUncheckAll.click();
    });
  });

  [
    {selectedTags: [tags[5], tags[9]], expectedPedigreeCounts: []},
    {selectedTags: [tags[3], tags[7], tags[8], tags[13], tags[14]], expectedPedigreeCounts: []}
  ].forEach(data => {
    it('should select a multiple tags and check if nothing found is shown', () => {
      page.familiesByPedigreeTab.click();
      page.openPedigreeTagsModal.click();
      data.selectedTags.forEach(tag => {
        page.findTag(tag).click();
        page.selectedTagsHeader.contains(tag);
      });
      cy.get('body').click(0, 0);

      page.pedigreesNothingFound.should('exist');
      page.openPedigreeTagsModal.click();
      page.pedigreeTagsModalUncheckAll.click();
    });
  });

  it('should check pedigree chart modal content', () => {
    page.familiesByPedigreeTab.click();
    page.pedigreeCells.each((cell) => {
      cy.wrap(cell).click();
      page.pedigreeModalContent.should('be.visible');
      page.pedigreeModalChart.should('be.visible');
      page.pedigreeModalCount.should('be.visible');
      page.pedigreeModalDownloadBtn.should('be.visible');
      page.pedigreeModalFamilyIds.should('not.be.empty');

      cy.get('body').click(30, 30);
      page.pedigreeModalChart.should('not.exist');
      page.pedigreeModalCount.should('not.exist');
      page.pedigreeModalDownloadBtn.should('not.exist');
      page.pedigreeModalFamilyIds.should('not.exist');
      page.pedigreeModalContent.should('not.exist');
    });
  });

  it('should check the count of pedigree chart family ids', () => {
    page.familiesByPedigreeTab.click();
    page.pedigreeCells.each((cell) => {
      cy.wrap(cell).click({force: true});
      page.pedigreeModalFamilyIds.invoke('text').then((text) => {
        let ids: string[] = [];
        ids = text.split(',');
        page.pedigreeModalCount.invoke('text').then(parseInt).should('eq', ids.length);
      });
      cy.get('body').click(-30, -30, {force: true});
    });
  });

  [
    {index: 0, name: 'first'},
    {index: 1, name: 'second'},
    {index: 5, name: 'fifth'}
  ].forEach(cell => {
    it(`should download family counters report from ${cell.name} pedigree modal`, () => {
      page.familiesByPedigreeTab.click();
      page.pedigreeCells.eq(cell.index).click({force: true});

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/families.ped';
      const expectedVariantsPath = `cypress/fixtures/variant-reports/families${cell.index}.ped`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.pedigreeModalDownloadBtn.click();
      });


      cy.readFile(downloadedVariantsPath, 'utf8')
        .then((downloadedFile: string) => {
          const downloadedFileObjects = [];
          const downloadedFileLines: string[] = downloadedFile.split(/\r\n|\r|\n/);
          const keys = downloadedFileLines[0].split('\t');
          for (let i = 1; i < downloadedFileLines.length - 1; i++) {
            const values = downloadedFileLines[i].split('\t');
            const obj = {};
            for (let j = 0; j < keys.length; j++) {
              if (j !== 8) { // NOTE: This is due to known issue in GPF, for now it's best to be ignored
                obj[keys[j]] = values[j];
              }
            }
            downloadedFileObjects.push(obj);
          }
          cy.readFile(expectedVariantsPath, 'utf8')
            .then((expectedFile: string) => {
              const expectedFileLines: string[] = expectedFile.split(/\r\n|\r|\n/);
              const expectedVariantsObjects = [];
              const expectedKeys = expectedFileLines[0].split('\t');
              for (let i = 1; i < expectedFileLines.length - 1; i++) {
                const values = expectedFileLines[i].split('\t');
                const obj = {};
                for (let j = 0; j < expectedKeys.length; j++) {
                  if (j !== 8) { // NOTE: This is due to known issue in GPF, for now it's best to be ignored
                    obj[expectedKeys[j]] = values[j];
                  }
                }
                expectedVariantsObjects.push(obj);
              }
              expect(downloadedFileObjects).to.deep.equal(expectedVariantsObjects);
            });
        });
    });
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
        cy.get('@tds').eq((data.rowIndex * 3) + i).should('have.text', data.expectedCounts[i]);
      }
    });
  });

  it('should display the correct numbers in families by pedigree of affected status', () => {
    const expectedValues: string[] = ['877', '789', '500', '128', '107', '106', '6', '3'];
    page.familiesByNumberTab.click();
    page.familiesByPedigreeDivs.each((ele, i) => {
      expect(ele.text()).to.eq(expectedValues[i]);
    });
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
