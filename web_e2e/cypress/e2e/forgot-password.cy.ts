import { ForgotPasswordPage } from 'cypress/elements/forgot-password-page';
import { UsersPage } from '../elements/users-page';

describe('Forgotten password tests', () => {
  const page = new ForgotPasswordPage();
  const usersPage = new UsersPage();

  before(() => {
    page.cleanup();
  });

  it('should open forgotten password window', () => {
    page.navigateToHome(false);

    cy.window().then((win) => {
      cy.stub(win, 'open', url => {
        win.location.href = `${Cypress.config().baseUrl}accounts/login/?next=/gpf/o/authorize/%3F${url}`;
      }).as('popup');
    });

    page.forgottenPasswordButton.should('not.exist');

    usersPage.loginButton.click();
    page.forgottenPasswordButton.should('be.visible');

    page.forgottenPasswordButton.click();
    cy.get('@popup').should('be.called');
  });
});
