import { RegistrationPage } from 'cypress/elements/registration-page';
import { UsersPage } from 'cypress/elements/users-page';

describe('Register tests', () => {
  const registrationPage = new RegistrationPage();
  const usersPage = new UsersPage();

  it('should open register window', () => {
    registrationPage.navigateToHome();
    usersPage.loginDropdownToggleButton.click();
    registrationPage.window.should('not.exist');

    usersPage.registerButton.click();
    registrationPage.window.should('be.visible');
  });
});
