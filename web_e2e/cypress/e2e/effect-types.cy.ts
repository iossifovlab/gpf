import { EffectTypesPage } from 'cypress/elements/effect-types-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Effect types tests', () => {
  const page = new EffectTypesPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display error alert when none of the checkboxes are selected', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'None').click();
    page.findErrorAlertInComponent('gpf-effect-types').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
    page.findErrorAlertInComponent('gpf-effect-types').should('not.exist');
  });

  it('should check/uncheck effect types checkboxes using "All" and "None" buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each(element => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each(element => {
      cy.wrap(element).should('be.checked');
    });
  });

  it('should test checkboxes using "UTRs" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'UTRs').click();
    cy.get('input').eq(14).should('be.checked');
    cy.get('input').eq(14).siblings().first().should('have.text', '3\'UTR');
    cy.get('input').eq(15).should('be.checked');
    cy.get('input').eq(15).siblings().first().should('have.text', '5\'UTR');

    [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].forEach(index => {
      cy.get('input').eq(index).should('not.be.checked');
    });
  });

  it('should test checkboxes using "LGDs" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'LGDs').click();
    let i = 2;
    genotypeBlockPage.effectTypesGroups.get('LGDs').forEach(element => {
      cy.get('input').eq(i).should('be.checked');
      cy.get('input').eq(i).siblings().first().should('have.text', element);
      i++;
    });

    [6, 7, 8, 9, 10, 11, 12, 13, 14, 15].forEach(index => {
      cy.get('input').eq(index).should('not.be.checked');
    });
  });

  it('should test checkboxes using "Nonsynonymous" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'Nonsynonymous').click();
    let i = 2;
    genotypeBlockPage.effectTypesGroups.get('Nonsynonymous').forEach(element => {
      cy.get('input').eq(i).should('be.checked');
      cy.get('input').eq(i).siblings().first().should('have.text', element);
      i++;
    });

    [10, 11, 12, 13, 14, 15].forEach(index => {
      cy.get('input').eq(index).should('not.be.checked');
    });
  });

  it('should test checkboxes using "Coding" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'Coding').click();
    let i = 2;
    genotypeBlockPage.effectTypesGroups.get('Coding').forEach(element => {
      cy.get('input').eq(i).should('be.checked');
      cy.get('input').eq(i).siblings().first().should('have.text', element);
      i++;
    });

    [11, 12, 13, 14, 15].forEach(index => {
      cy.get('input').eq(index).should('not.be.checked');
    });
  });
});
