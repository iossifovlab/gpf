import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';
import { PhenoBrowserPage } from 'cypress/elements/pheno-browser-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Datasets tests', () => {
  const page = new DatasetsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
  });

  beforeEach(() => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics, false);
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

  it('should change url correctly after clicking on a dataset from the dataset dropdown menu', () => {
    const datasets = [
      {id: datasetIds.allGenotypes, url: "ALL_genotypes"},
      {id: datasetIds.compGenotypes, url: "COMP_genotypes"},
      {id: datasetIds.compDenovo, url: "comp_denovo"},
      {id: datasetIds.compVcf, url: "comp_vcf"},
      {id: datasetIds.compAll, url: "comp_all"},
      {id: datasetIds.iossifov2014, url: "iossifov_2014"},
      {id: datasetIds.multi, url: "multi"}
    ]

    page.loginAdmin();

    datasets.forEach(dataset => {
      page.datasetsDropdownMenuButton.click();
      page.datasetsDropdownMenuElements.should('be.visible');
      page.datasetsDropdownMenuElements.contains(dataset.id).click();
      cy.url().then(url => {
        expect(url).to.contain(Cypress.config().baseUrl + 'datasets/' + dataset.url + '/');
      });
    });
  });
});

describe('Datasets Iossifov dataset count tests', () => {
  const page = new DatasetsPage();

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
      page.familiesByNumberDropdownButton.select('Role');

      page.allFamiliesByNumberHeaderCells.eq(data.rowIndex).should('have.text', data.roleId);

      page.allFamiliesByNumberDataCells.as('tds');
      for (let i = 0; i < data.expectedCounts.length; i++) {
        cy.get('@tds').eq((data.rowIndex * 3) + i).should('have.text', data.expectedCounts[i])
      }
    });
  });

  it('should display the correct numbers in families by pedigree of affected status', () => {
    const expectedValues: string[] = ['877', '789', '500', '128', '107', '106', '6', '14658, 11299, 11633'];
    page.familiesByPedigreeDivs.each((ele, i) => {
      expect(ele.text()).to.eq(expectedValues[i]);
    })
  });

  [
    {effectType: 'LGDs', expectedCounts: ['393, 0.157', '(366, 15%)', '180, 0.094', '(169, 9%)']},
    {effectType: 'UTRs', expectedCounts: ['244, 0.097', '(237, 9%)', '154, 0.081', '(144, 8%)']},
    {effectType: 'Missense', expectedCounts: ['1680, 0.67', '(1185, 47%)', '1149, 0.602', '(843, 44%)']},
    {effectType: 'Intron', expectedCounts: ['821, 0.327', '(671, 27%)', '558, 0.292', '(464, 24%)']}
  ].forEach(data => {
    it('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" role table', () => {
      page.denovoVariantsDropdownButton.select('Role');
      page.findDenovoVariantsCountsByRowName(data.effectType).each((ele, i) => {
        expect(ele.text()).to.eq(data.expectedCounts[i]);
      });
    });
  });

  [
    {effectType: 'LGDs', expectedCounts: ['393, 0.157', '(366, 15%)', '180, 0.094', '(169, 9%)']},
    {effectType: 'UTRs', expectedCounts: ['244, 0.097', '(237, 9%)', '154, 0.081', '(144, 8%)']},
    {effectType: 'Missense', expectedCounts: ['1680, 0.67', '(1185, 47%)', '1149, 0.602', '(843, 44%)']},
    {effectType: 'Intron', expectedCounts: ['821, 0.327', '(671, 27%)', '558, 0.292', '(464, 24%)']}
  ].forEach(data => {
    it('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" status table', () => {
      page.denovoVariantsDropdownButton.select('Affected Status');
      page.findDenovoVariantsCountsByRowName(data.effectType).each((ele, i) => {
        expect(ele.text()).to.eq(data.expectedCounts[i]);
      });
    });
  });
});

describe('Datasets visual tests', () => {
  const page = new DatasetsPage();

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
    cy.get('#families-by-number-div').matchImageSnapshot('iossifov-family-table-status');

    page.familiesByNumberDropdownButton.select('Role');
    cy.get('#families-by-number-div').matchImageSnapshot('iossifov-family-table-role');

    page.familiesByNumberDropdownButton.select('Phenotype');
    cy.get('#families-by-number-div').matchImageSnapshot('iossifov-family-table-phenotype');
  });

  it('should compare families by pedigree table data', () => {
    cy.get('#families-by-pedigree-div').scrollIntoView().matchImageSnapshot('iossifov-pedigree-table-status');

    cy.get('.col-sm-3 > .select-wrapper > .form-control').select('Role');
    page.familiesByPedigreeDivs.should('have.length', 8);
    cy.get('#families-by-pedigree-div').scrollIntoView().matchImageSnapshot('iossifov-pedigree-table-role');

    cy.get('.col-sm-3 > .select-wrapper > .form-control').select('Phenotype');
    page.familiesByPedigreeDivs.should('have.length', 8);
    cy.get('#families-by-pedigree-div').scrollIntoView().matchImageSnapshot('iossifov-pedigree-table-phenotype');
  });

  it('should compare de novo variants table data', () => {
    cy.get('#denovo-variants-div').scrollIntoView().matchImageSnapshot('iossifov-denovo-table-status');

    page.denovoVariantsDropdownButton.select('Role');
    cy.get('#denovo-variants-div').scrollIntoView().matchImageSnapshot('iossifov-denovo-table-role');

    page.denovoVariantsDropdownButton.select('Phenotype');
    cy.get('#denovo-variants-div').scrollIntoView().matchImageSnapshot('iossifov-denovo-table-phenotype');
  });
});
