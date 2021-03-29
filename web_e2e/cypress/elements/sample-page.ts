import { UsersPage } from "./users-page";

export class AppPage{
  get title() {
    return cy.get('#title');
  }

  login(username: string, password: string) {
    const usersPage = new UsersPage();

    if (!username || !password) {
      return;
    }

    usersPage.loginDropdownToggleButton.click();
    usersPage.usernameInput.type(username);
    usersPage.passwordInput.type(password);
    usersPage.loginSubmitButton.click();
  }
}
