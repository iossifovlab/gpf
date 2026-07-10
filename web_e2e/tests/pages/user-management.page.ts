import { Locator, Page } from '@playwright/test';

// Page object for the `/management` surface: the Users / Groups / Datasets
// tables, create forms, per-entity cells and the shared add-item menu.
export class UserManagementPage {
  public readonly usersTable: Locator;
  public readonly groupsTable: Locator;
  public readonly gridCell: Locator;
  public readonly searchField: Locator;

  // Create-user form.
  public readonly createUserFormButton: Locator;
  public readonly createContainer: Locator;
  public readonly nameBox: Locator;
  public readonly emailBox: Locator;
  public readonly createUserButton: Locator;
  public readonly cancelUserCreationButton: Locator;
  public readonly cancelButton: Locator;

  // Create-group form.
  public readonly createGroupFormButton: Locator;
  public readonly groupNameBox: Locator;
  public readonly createGroupButton: Locator;
  public readonly cancelGroupCreationButton: Locator;

  // Add-item menu.
  public readonly addItemButton: Locator;
  public readonly searchMenuTextbox: Locator;

  // Confirm action buttons.
  public readonly addButton: Locator;
  public readonly removeConfirm: Locator;
  public readonly deleteConfirm: Locator;
  public readonly resetConfirm: Locator;

  public constructor(private readonly page: Page) {
    this.usersTable = page.locator('gpf-users-table');
    this.groupsTable = page.locator('gpf-groups-table');
    this.gridCell = page.locator('.grid-cell');
    this.searchField = page.locator('#search-field');

    this.createUserFormButton = page.locator('#create-user-form-button');
    this.createContainer = page.locator('.create-container');
    this.nameBox = page.locator('#name-box');
    this.emailBox = page.locator('#email-box');
    this.createUserButton = page.locator('#create-user-button');
    this.cancelUserCreationButton = page.locator('#cancel-user-creation-button');
    this.cancelButton = page.locator('#cancel-button');

    this.createGroupFormButton = page.locator('#create-group-form-button');
    this.groupNameBox = page.locator('#group-name-box');
    this.createGroupButton = page.locator('#create-group-button');
    this.cancelGroupCreationButton = page.locator('#cancel-group-creation-button');

    this.addItemButton = page.locator('.add-item-button');
    this.searchMenuTextbox = page.getByRole('textbox', { name: 'Search' });

    this.addButton = page.getByRole('button', { name: 'Add' });
    this.removeConfirm = page.getByRole('button', { name: 'Remove', exact: true });
    this.deleteConfirm = page.getByRole('button', { name: 'Delete', exact: true });
    this.resetConfirm = page.locator('button:text("Reset")');
  }

  // --- Nav ---
  // A management nav anchor by text ('Management', 'Users', 'Groups').
  public navLink(name: string): Locator {
    return this.page.locator(`a:text("${name}")`);
  }

  // The 'Datasets' management tab (rendered as a tab, not an anchor).
  public datasetsTab(): Locator {
    return this.page.getByRole('tab', { name: 'Datasets' });
  }

  // --- Cells (keyed by entity id: email, group name or dataset id) ---
  public userCell(email: string): Locator {
    return this.page.locator(`[id="${email}-user-cell"]`);
  }

  public groupCell(name: string): Locator {
    return this.page.locator(`[id="${name}-group-cell"]`);
  }

  public groupsCell(entity: string): Locator {
    return this.page.locator(`[id="${entity}-groups-cell"]`);
  }

  public datasetsCell(entity: string): Locator {
    return this.page.locator(`[id="${entity}-datasets-cell"]`);
  }

  public usersCell(entity: string): Locator {
    return this.page.locator(`[id="${entity}-users-cell"]`);
  }

  public usersListCell(entity: string): Locator {
    return this.page.locator(`[id="${entity}-users-list-cell"]`);
  }

  public passwordCell(email: string): Locator {
    return this.page.locator(`[id="${email}-password-cell"]`);
  }

  public resetPasswordButton(email: string): Locator {
    return this.page.locator(`[id="${email}-reset-password-button"]`);
  }

  public deleteUserButton(email: string): Locator {
    return this.page.locator(`[id="${email}-delete-user-button"]`);
  }

  public deleteGroupButton(name: string): Locator {
    return this.page.locator(`[id="${name}-delete-group-button"]`);
  }

  public newNameInput(email: string): Locator {
    return this.page.locator(`[id="${email}-new-name-input"]`);
  }

  // --- List items inside a cell ---
  // A `<item>-list-item` element inside the given cell.
  public listItem(cell: Locator, itemId: string): Locator {
    return cell.locator(`[id="${itemId}-list-item"]`);
  }

  // The confirm-button (delete/remove) for a list item inside a cell.
  public listItemConfirm(cell: Locator, itemId: string): Locator {
    return this.listItem(cell, itemId).locator('gpf-confirm-button');
  }

  // The 'Add' button inside a given cell.
  public addButtonIn(cell: Locator): Locator {
    return cell.getByRole('button', { name: 'Add' });
  }

  // An add-item menu button by its label (dataset/group/user id).
  public menuItem(name: string): Locator {
    return this.page.getByRole('button', { name });
  }
}
