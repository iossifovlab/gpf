import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { VariantReportsPage } from 'cypress/elements/variant-reports-page';

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
