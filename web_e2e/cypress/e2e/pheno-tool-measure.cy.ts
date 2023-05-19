import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

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

  it('should check whether when the measure is empty, an error message appears' +
     'and the normalization checkboxes get disabled', () => {
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');
    page.ageCheckbox.should('be.disabled');
    page.iqCheckbox.should('be.disabled');

    page.searchbox.click();
    page.getDropdownOptionByText('i1.m1').click();
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('not.exist');
    page.ageCheckbox.should('not.be.disabled');
    page.iqCheckbox.should('not.be.disabled');

    page.clearMeasureButton.click();
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');
    page.ageCheckbox.should('be.disabled');
    page.iqCheckbox.should('be.disabled');
  });

  it('should check if the normalization checkboxes get disabled when' +
     'the measure is the same as the normalization criteria', () => {
    page.searchbox.click();
    page.getDropdownOptionByText('i1.age').click();
    page.ageCheckbox.should('be.disabled');

    page.clearMeasureButton.click();
    page.searchbox.click();
    page.getDropdownOptionByText('i1.iq').click();
    page.iqCheckbox.should('be.disabled');
  });

  it('should check if the dropdown menu closes when clicking the remove button', () => {
    page.searchbox.click();
    page.dropdown.should('be.visible');
    page.clearMeasureButton.click();
    page.dropdown.should('not.be.visible');
  });

  it('should check if the dropdown menu closes when clicking outside', () => {
    page.searchbox.click();
    page.dropdown.should('be.visible');
    cy.get('body').click(-30, -30, {force: true});
    page.dropdown.should('not.be.visible');
  });

  it('should check the remove button with selected measure', () => {
    page.searchbox.click();
    page.dropdown.should('be.visible');
    page.getDropdownOptionByText('i1.iq').click();
    page.clearMeasureButton.click();
    page.searchbox.should('be.empty');
    page.dropdown.should('not.be.visible');
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
        page.getDropdownOptionByText(measure).should('exist');
      });
    });
  });
});
