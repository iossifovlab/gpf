import { ForgotPasswordPage } from 'cypress/elements/forgot-password-page';
import { UsersPage } from '../elements/users-page';

describe('Forgotten password tests', () => {
  const forgotPasswordPage = new ForgotPasswordPage();
  const usersPage = new UsersPage();

  it('should open forgotten password window', () => {
    forgotPasswordPage.navigateToHome();
    usersPage.loginDropdownToggleButton.click();
    forgotPasswordPage.window.should('not.exist');

    usersPage.forgottenPasswordButton.click();
    forgotPasswordPage.window.should('be.visible');
  });
});
