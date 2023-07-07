import { FederationCredentialsPage } from 'cypress/elements/federation-credentials-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Federation token tests', () => {
  const page = new FederationCredentialsPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.userProfile);
    page.federationTab.click();
  });

  it('should check federation tokens tab elements', () => {
    page.federationCredentials.should('be.visible');
    page.newCredentialInput.should('be.visible');
    page.createCredentialButton.should('be.visible');
    cy.get('div').contains('Name').should('be.visible');
    cy.get('div').contains('Actions').should('be.visible');
  });

  it('should create new credential', () => {
    page.newCredentialInput.type('TestCredentials');
    page.createCredentialButton.click();
    page.credentialsModal.should('be.visible');
    page.credentialsModal.contains('Credentials: shown only once, copy before closing.');
    page.copyCredentialsButton.click();
    page.credentials.should('not.be.empty');

    cy.get('body').click(0, 0);
    page.credentialsModal.should('not.exist');

    page.credentialNameCell('TestCredentials').should('be.visible');
    page.credentialClientIdCell('TestCredentials').should('not.be.empty');
    page.credentialClientSecretCell('TestCredentials').should('not.be.empty');
    page.credentialDeleteButton('TestCredentials').click();
    page.deleteCredentialConfirmButton.click();

    page.credentialNameCell('TestCredentials').should('not.exist');
  });

  it('should not create credential with invalid name', () => {
    page.newCredentialInput.type('a');
    page.createCredentialButton.click();
    page.InvalidNameError.should('be.visible');
    page.newCredentialInput.should('be.focused');
    page.credentialNameCell('a').should('not.exist');

    page.newCredentialInput.type('b');
    page.createCredentialButton.click();
    page.InvalidNameError.should('be.visible');
    page.newCredentialInput.should('be.focused');
    page.credentialNameCell('ab').should('not.exist');
  });

  it('should not create credential with existing name', () => {
    page.newCredentialInput.type('ExistingCredential');
    page.createCredentialButton.click();

    page.credentialsModal.should('be.visible');
    cy.get('body').click(0, 0);
    page.credentialsModal.should('not.exist');

    page.credentialNameCell('ExistingCredential').should('be.visible');

    page.newCredentialInput.type('ExistingCredential');
    page.createCredentialButton.click();
    page.existingNameError.should('be.visible');
    page.newCredentialInput.clear();

    page.credentialDeleteButton('ExistingCredential').click();
    page.deleteCredentialConfirmButton.click();
  });
});
