import { RegistrationPage } from 'cypress/elements/registration-page';
import { UsersPage } from 'cypress/elements/users-page';

describe('Register tests', () => {
  const page = new RegistrationPage();
  const usersPage = new UsersPage();

  before(() => {
    page.cleanup();
  });

  it('should open register window', () => {
    page.navigateToHome(false);
    usersPage.loginDropdownToggleButton.click();
    page.window.should('not.exist');

    usersPage.registerButton.click();
    page.window.should('be.visible');
  });
});
