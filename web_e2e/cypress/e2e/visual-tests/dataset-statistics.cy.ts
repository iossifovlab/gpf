import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { VariantReportsPage } from 'cypress/elements/variant-reports-page';

describe('Dataset statistics visual tests', () => {
  const variantReportsPage = new VariantReportsPage();

  before(() => {
    variantReportsPage.cleanup();
    variantReportsPage.navigateToHome(false);
    variantReportsPage.loginAdmin();
  });

  beforeEach(() => {
    variantReportsPage.preserveLogin();
    variantReportsPage.navigateToHome();
    variantReportsPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
  });

  it('should compare family by number table data', () => {
    variantReportsPage.familiesByNumberTab.click();
    variantReportsPage.familiesByNumber.matchImageSnapshot('iossifov-family-table-status');

    variantReportsPage.familiesByNumberSelect.select('Role');
    variantReportsPage.familiesByNumber.matchImageSnapshot('iossifov-family-table-role');

    variantReportsPage.familiesByNumberSelect.select('Phenotype');
    variantReportsPage.familiesByNumber.matchImageSnapshot('iossifov-family-table-phenotype');
  });


  it('should compare families by pedigree table data', () => {
    variantReportsPage.familiesByPedigreeTab.click();

    variantReportsPage.pedigreeCells.should('have.length', 8);
    variantReportsPage.familiesByPedigreeTable.matchImageSnapshot('iossifov-pedigree-table-status');

    variantReportsPage.familiesByPedigreeSelect.select('Role');
    variantReportsPage.pedigreeCells.should('have.length', 8);
    variantReportsPage.familiesByPedigreeTable.matchImageSnapshot('iossifov-pedigree-table-role');

    variantReportsPage.familiesByPedigreeSelect.select('Phenotype');
    variantReportsPage.pedigreeCells.should('have.length', 8);
    variantReportsPage.familiesByPedigreeTable.matchImageSnapshot('iossifov-pedigree-table-phenotype');
  });

  it.only('should compare de novo variants table data', { scrollBehavior: false }, () => {
    variantReportsPage.deNovoVariantsTab.click();

    // cy.document().matchImageSnapshot('iossifov-denovo-table-status', { capture: 'fullPage'});
    // variantReportsPage.denovoVariants.matchImageSnapshot('iossifov-denovo-table-status');

    // variantReportsPage.denovoVariantsSelect.select('Role');
    // cy.document().matchImageSnapshot('iossifov-denovo-table-role', { capture: 'fullPage'});


    variantReportsPage.denovoVariantsSelect.select('Phenotype');
    cy.document().matchImageSnapshot('iossifov-denovo-table-phenotype', { capture: 'fullPage'});

    // variantReportsPage.denovoVariants.matchImageSnapshot('iossifov-denovo-table-phenotype', { capture: 'fullPage'});
  });
});