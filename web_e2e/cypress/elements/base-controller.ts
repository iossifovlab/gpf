import { BasePage } from './utils';

export class BaseController {
  private basePage = new BasePage();

  public navigateToHome(): void {
    this.basePage.navigateToHome();
  }

  public loginAdmin(): void {
    this.basePage.loginAdmin();
  }

  public login(username: string, password: string): void {
    this.basePage.login(username, password);
  }

  public logout(): void {
    this.basePage.logout();
  }

  public cleanup(): void {
    this.basePage.cleanup();
  }

  public preserveLogin(): void {
    this.basePage.preserveLogin();
  }
}