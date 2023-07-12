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

    page.forgottenPasswordButton.should('not.exist');

    usersPage.logInButton.click();
    page.forgottenPasswordButton.should('be.visible');

    page.forgottenPasswordButton.click();

    page.inputEmailField.should('be.visible');
    page.resetPasswordButton.should('be.visible');
  });
});
