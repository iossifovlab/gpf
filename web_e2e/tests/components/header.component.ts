import { Locator, Page } from '@playwright/test';

// Component object for the global `#header` navigation bar.
export class Header {
  public readonly root: Locator;
  public readonly navLinks: Locator;
  public readonly logInButton: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('#header');
    this.navLinks = this.root.locator('a');
    this.logInButton = page.locator('#log-in-button');
  }

  // A header navigation anchor by its visible text (e.g. 'Gene Profiles').
  public navLink(name: string): Locator {
    return this.root.locator(`a:text("${name}")`);
  }

  // A header navigation anchor matched via getByText (used for counting /
  // visibility of individual tabs).
  public navLinkByText(name: string): Locator {
    return this.navLinks.getByText(name);
  }

  // A per-dataset tool tab `li` (e.g. 'Gene Browser', 'Dataset Statistics').
  // Carries the `nav-item disabled-tool` class when the tool is disabled.
  public toolNavItem(name: string): Locator {
    return this.page.locator('li').filter({ hasText: name });
  }
}
