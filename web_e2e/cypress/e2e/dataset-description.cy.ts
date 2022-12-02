import { DatasetDescriptionPage } from 'cypress/elements/dataset-description-page';
import { DatasetsPage } from 'cypress/elements/datasets-page';
import { UserManagementPage } from 'cypress/elements/user-management-page';
import { datasetIds, sidenavPageLinks, toolPageLinks, userData } from 'cypress/elements/utils';

describe('Dataset description tests', () => {
  const page = new DatasetDescriptionPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetDescription);
  });

  it('should display dataset description window', () => {
    page.window.should('be.visible');
  });

  it('should display empty description placeholder text', () => {
    page.emptyDescriptionPlaceholder.should('be.visible');
    page.emptyDescriptionPlaceholder.should(
      'have.text',
      'Empty description. Write a description using the pencil button to the right.'
    );
  });

  it('should display edit icon', () => {
    page.editIcon.should('be.visible')
  });

  it('should display angular markdown editor after clicking the edit button', () => {
    page.editorWindow.should('not.exist');
    page.editIcon.click();
    page.editorWindow.should('be.visible');
  });

  it('should display preview button', () => {
    page.editorPrevieButton.should('not.exist');
    page.editIcon.click();
    page.editorPrevieButton.should('be.visible');
  });

  it('should display save button', () => {
    page.editorSaveButton.should('not.exist');
    page.editIcon.click();
    page.editorSaveButton.should('be.visible');
  });

  it('should display close button', () => {
    page.editorCloseButton.should('not.exist');
    page.editIcon.click();
    page.editorCloseButton.should('be.visible');
  });

  it('should display the editor header bar', () => {
    page.editorHeader.should('not.exist');
    page.editIcon.click();
    page.editorHeader.should('be.visible');
  });

  it('should hide the edit button after clicking it', () => {
    page.editIcon.should('be.visible');
    page.editIcon.click();
    page.editIcon.should('not.exist');
    page.editorCloseButton.click();
    page.editIcon.should('be.visible');
  });

  it('should save some description and than delete it and check whether the description' +
     'returns to the empty placeholder text', () => {
    page.emptyDescriptionPlaceholder.should('be.visible');
    page.editIcon.click();
    page.editorTextarea.type('TEST DESCRIPTION');
    page.editorSaveButton.click();
    page.emptyDescriptionPlaceholder.should('not.exist');
    page.clearDescription();
  });

  it('should save the markdown', () => {
    page.emptyDescriptionPlaceholder.should('be.visible');
    page.descriptionText.should('not.exist');
    page.editIcon.click();
    page.editorTextarea.type('TEST DESCRIPTION ASDF');
    page.editorSaveButton.click();
    page.descriptionText.should('have.text', 'TEST DESCRIPTION ASDF');
    page.clearDescription();
  });
});

describe('Dataset description access rights tests', () => {
  const page = new DatasetDescriptionPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
  });

  it('should always show the dataset description button if the user is admin', () => {
    const datasetsPage = new DatasetsPage();

    page.loginAdmin();

    page.navigateToDatasetPage(datasetIds.allGenotypes, toolPageLinks.geneBrowser);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.geneBrowser);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compDenovo, toolPageLinks.datasetStatistics);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.navigateToDatasetPage(datasetIds.multi, toolPageLinks.datasetStatistics);
    datasetsPage.datasetDescriptionButton.should('be.visible');

    page.logout();
  });

  it('should NOT show the dataset description button for a regular user when no description is available', () => {
    const datasetsPage = new DatasetsPage();

    page.login(userData.normal.username, userData.normal.password, false);

    page.navigateToDatasetPage(datasetIds.allGenotypes, toolPageLinks.geneBrowser, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.geneBrowser, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compDenovo, toolPageLinks.datasetStatistics, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.navigateToDatasetPage(datasetIds.multi, toolPageLinks.datasetStatistics, false);
    datasetsPage.datasetDescriptionButton.should('not.exist');

    page.logout();
  });


  it('should log admin, give researcher user access rights for iossifov_2014,' +
     'create dataset description for iossifov_2014, log researcher user and check' +
     'whether the newly created description exists and that it cannot be edited', () => {
    const userManagementPage = new UserManagementPage();

    // give researcher access for iossifov_2014
    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    userManagementPage.getUserEditorButtonByEmail(userData.normal.username).click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownSearch.type('iossifov');
    userManagementPage.userWindowGroupDropdownListCheckboxes.first().click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowSubmitButton.click();

    page.navigateToSidenavPage(sidenavPageLinks.datasets);
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetDescription);
    page.editIcon.click();
    page.editorTextarea.type('IOSSIFOV TEST DESCRIPTION');
    page.editorSaveButton.click();
    page.logout();

    page.login(userData.normal.username, userData.normal.password);
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetDescription);
    page.descriptionText.should('have.text', 'IOSSIFOV TEST DESCRIPTION');
    page.editIcon.should('not.exist');
    page.logout();

    // state cleanup
    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    userManagementPage.getUserEditorButtonByEmail(userData.normal.username).click();
    userManagementPage.allUserEditGroupRemoveButtons.first().click();
    userManagementPage.userWindowSubmitButton.click();
    page.navigateToSidenavPage(sidenavPageLinks.datasets);
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetDescription);
    page.clearDescription();
    page.logout();
  });

  it('should login regular user, try to navgigate to a dataset description page without description via the url' +
     'and get redirected back to the home page', () => {
    const homePageUrl = `${Cypress.config().baseUrl}datasets/ALL_genotypes/${toolPageLinks.geneBrowser}`;
    const datasetDescriptionUrl =
      `${Cypress.config().baseUrl}datasets/ALL_genotypes/${toolPageLinks.datasetDescription}`;

    page.login(userData.normal.username, userData.normal.password, false);
    cy.visit(datasetDescriptionUrl);
    cy.url().should('eq', homePageUrl);
    page.logout();
  });
});
