import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { measureMemory } from 'vm';

describe('Pheno tool measure tests', () => {
  const page = new PhenoToolMeasurePage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
  });

  it('should display error alert when measure searchbox is empty', () => {
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('not.exist');
  });

  it('should check if Age checkbox is disabled', () => {
    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();
    page.block.contains('Age').find('input[type="checkbox"]').should('be.disabled');
  });

  it('should check if Non verbal IQ checkbox is disabled', () => {
    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.iq').click();
    page.block.contains('Non verbal IQ').find('input[type="checkbox"]').should('be.disabled');
  });

  it('should check if the dropdown menu closes when clicking the remove button', () => {
    page.searchbox.click();
    page.dropdown.should('be.visible');
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', '×').click();
    page.dropdown.should('not.exist');
  });

  it('should check if the dropdown menu closes when clicking outside', () => {
    page.searchbox.click();
    page.dropdown.should('be.visible');
    cy.get('body').click(-30, -30, {force: true});
    page.dropdown.should('not.exist');
  });

  it('should check the remove button with selected measure', () => {
    page.searchbox.click();
    page.dropdown.should('be.visible');
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.iq').click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', '×').click();
    page.searchbox.should('be.empty');
    page.dropdown.should('not.exist');
  });

  [
    {searchText: 'age', options: ['i1.age']},
    {searchText: 'm', options: ['i1.m1', 'i1.m2', 'i1.m3', 'i1.m4']},
    {searchText: 'q', options: ['i1.iq']},
  ].forEach(data => {
    it('should type and check available measures', () => {
      page.searchbox.click();
      page.searchbox.type(data.searchText);
      data.options.forEach(measure => {
        page.findButtonInComponentContainingText('gpf-pheno-measure-selector', measure).should('exist');
      });
    });
  });
});
