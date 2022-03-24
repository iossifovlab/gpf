import { ForgotPasswordPage } from 'cypress/elements/forgot-password-page';
import { UsersPage } from '../elements/users-page';

describe('Forgotten password tests', () => {
  const page = new ForgotPasswordPage();
  const usersPage = new UsersPage();

  before(() => {
    page.cleanup();
  });

  it('should open forgotten password window', () => {
    page.navigateToHome();
    usersPage.loginDropdownToggleButton.click();
    page.window.should('not.exist');

    usersPage.forgottenPasswordButton.click();
    page.window.should('be.visible');
  });
});
