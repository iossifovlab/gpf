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
    variantReportsPage.prepareForVisualTest();
  });

  it('should compare family by number table data', () => {
    variantReportsPage.familiesByNumberTab.click();
    cy.matchImage();

    variantReportsPage.familiesByNumberSelect.select('Role');
    cy.matchImage();

    variantReportsPage.familiesByNumberSelect.select('Phenotype');
    cy.matchImage();
  });


  it('should compare families by pedigree table data', () => {
    variantReportsPage.familiesByPedigreeTab.click();
    variantReportsPage.pedigreeCells.should('have.length', 8);
    cy.matchImage();

    variantReportsPage.familiesByPedigreeSelect.select('Role');
    variantReportsPage.pedigreeCells.should('have.length', 8);
    cy.matchImage();

    variantReportsPage.familiesByPedigreeSelect.select('Phenotype');
    variantReportsPage.pedigreeCells.should('have.length', 8);
    cy.matchImage();
  });

  it('should compare de novo variants table data', () => {
    variantReportsPage.deNovoVariantsTab.click();
    cy.matchImage();

    variantReportsPage.denovoVariantsSelect.select('Role');
    cy.matchImage();

    variantReportsPage.denovoVariantsSelect.select('Phenotype');
    cy.matchImage();
  });
});