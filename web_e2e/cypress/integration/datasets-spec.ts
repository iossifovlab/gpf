import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';
import { PhenoBrowserPage } from 'cypress/elements/pheno-browser-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Datasets tests', () => {
  const page = new DatasetsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
  });

  beforeEach(() => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
  });

  afterEach(() => {
    page.logout();
  });

  it('should toggle studies dropdown menu', () => {
    page.loginAdmin();
    page.datasetsDropdownMenuButton.invoke('attr', 'aria-expanded').should('contain', 'false');
    page.datasetsDropdownMenuButton.click();
    page.datasetsDropdownMenuButton.invoke('attr', 'aria-expanded').should('contain', 'true');
    page.datasetsDropdownMenuButton.click();
    page.datasetsDropdownMenuButton.invoke('attr', 'aria-expanded').should('contain', 'false');
  });

  it('should display genotype browser', () => {
    const genotypeBrowserPage = new GenotypeBrowserPage();

    page.loginAdmin();
    genotypeBrowserPage.window.should('not.exist');

    page.genotypeBrowserButton.click();
    genotypeBrowserPage.window.should('be.visible');
  });

  it('should display dataset statistics window', () => {
    page.loginAdmin();
    page.datasetStatisticsWindow.should('be.visible');

    page.genotypeBrowserButton.click();
    page.datasetStatisticsWindow.should('not.exist');

    page.datasetStatisticsButton.click();
    page.datasetStatisticsWindow.should('be.visible');
  });

  it('should display phenotype browser window', () => {
    const phenoBrowserPage = new PhenoBrowserPage();

    page.loginAdmin();
    phenoBrowserPage.window.should('not.exist');

    page.phenotypeBrowserButton.click();
    phenoBrowserPage.window.should('be.visible');

    page.datasetStatisticsButton.click();
    phenoBrowserPage.window.should('not.exist');
  });

  it('should display phenotype tool window', () => {
    const phenoToolPage = new PhenoToolPage();

    page.loginAdmin();
    page.phenotypeToolButton.click();
    phenoToolPage.window.should('be.visible');

    page.datasetStatisticsButton.click();
    phenoToolPage.window.should('not.exist');
  });
});

describe('Iossifov dataset count tests', () => {
  const page = new DatasetsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
  });

  [{roleId: 'mom', expectedCounts: ['0', '2516', '2516']},
   {roleId: 'dad', expectedCounts: ['2516', '0', '2516']},
   {roleId: 'proband', expectedCounts: ['2166', '341', '2507']},
   {roleId: 'sibling', expectedCounts: ['899', '1011', '1910']}
  ].forEach((data) => {
    it('should display the correct numbers in families by numbers of role - \'' + data.roleId + '\'', () => {
      page.familiesByNumberDropdownButton.select('Role');

      page.allFamiliesByNumberHeaderCells.invoke('text').then((text) => {
        const roles = text.split('  ').map(str => str.trim());
        const indexOfRoleId = roles.indexOf(data.roleId);
        page.allFamiliesByNumberDataCells.as('tds');

        for (let i = 0; i < data.expectedCounts.length; i++) {
          cy.get('@tds').eq(indexOfRoleId * 3 + i).invoke('text').then(text => expect(text.trim()).to.eq(data.expectedCounts[i]));
        }
      });
    });
  });

  it('should display the correct numbers in families by pedigree of affected status', () => {
    const expectedValues: number[] = [6, 877, 789, 500, 128, 107, 106, 14658, 11299, 11633];

    page.familiesByPedigreeDivs.invoke('text').then(text => {
      let familiesByPedigreeValues = text.split(',').join(' ').split('  ').map(a => a.trim()).map(Number);

      familiesByPedigreeValues.sort((a, b) =>  a - b);
      expectedValues.sort((a, b) =>  a - b);

      expect(familiesByPedigreeValues).to.deep.equal(expectedValues);
    });
  });

  [{effectType: 'LGDs', expectedCounts: ['180, 0.094', '(169, 9%)', '393, 0.157', '(366, 15%)']},
   {effectType: 'UTRs', expectedCounts: ['154, 0.081', '(144, 8%)', '244, 0.097', '(237, 9%)']},
   {effectType: 'Missense', expectedCounts: ['1149, 0.602', '(843, 44%)', '1680, 0.67', '(1185, 47%)']},
   {effectType: 'Intron', expectedCounts: ['558, 0.292', '(464, 24%)', '821, 0.327', '(671, 27%)']}
  ].forEach((data) => {
    it('should display the correct numbers for ' + data.effectType +
       ' effectType in the \'Denovo variants of:\' role table', () => {
      page.denovoVariantsDropdownButton.select('Role');
      page.findDenovoVariantsCountsByRowName(data.effectType).invoke('text').then(text => {
        const denovoVariantsCounts = text.split('  ').map(a => a.trim());

        denovoVariantsCounts.sort();
        data.expectedCounts.sort();

        expect(denovoVariantsCounts).to.deep.eq(data.expectedCounts);
      });
    });
  });

  [{effectType: 'LGDs', expectedCounts: ['180, 0.094', '(169, 9%)', '393, 0.157', '(366, 15%)']},
   {effectType: 'UTRs', expectedCounts: ['154, 0.081', '(144, 8%)', '244, 0.097', '(237, 9%)']},
   {effectType: 'Missense', expectedCounts: ['1149, 0.602', '(843, 44%)', '1680, 0.67', '(1185, 47%)']},
   {effectType: 'Intron', expectedCounts: ['558, 0.292', '(464, 24%)', '821, 0.327', '(671, 27%)']}
  ].forEach((data) => {
    it('should display the correct numbers for ' + data.effectType +
       ' effectType in the \'Denovo variants of:\' status table', () => {
      page.denovoVariantsDropdownButton.select('Affected Status');
      page.findDenovoVariantsCountsByRowName(data.effectType).invoke('text').then(text => {
        const denovoVariantsCounts = text.split('  ').map(a => a.trim());

        denovoVariantsCounts.sort();
        data.expectedCounts.sort();

        expect(denovoVariantsCounts).to.deep.eq(data.expectedCounts);
      });
    });
  });
});
