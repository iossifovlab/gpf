import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-federation-credentials` tab (create /
// rename / delete federation tokens).
export class FederationCredentials {
  public readonly root: Locator;
  public readonly newCredentialNameBox: Locator;
  public readonly createCredentialButton: Locator;
  public readonly gridContainer: Locator;

  // Table headers and the delete-confirmation button.
  public readonly nameHeader: Locator;
  public readonly actionsHeader: Locator;
  public readonly deleteConfirm: Locator;

  // Creation modal.
  public readonly modalContent: Locator;
  public readonly credentialModal: Locator;
  public readonly credentialModalContent: Locator;
  public readonly copyClientSecret: Locator;
  public readonly copyClientId: Locator;

  // Rename controls.
  public readonly editIcon: Locator;
  public readonly cancelButton: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-federation-credentials');
    this.newCredentialNameBox = page.locator('#new-credential-name-box');
    this.createCredentialButton = page.locator('#create-credential-button');
    this.gridContainer = page.locator('.grid-container');

    this.nameHeader = page.getByText('Name', { exact: true });
    this.actionsHeader = page.getByText('Actions', { exact: true });
    this.deleteConfirm = page.getByRole('button', { name: 'Delete' });

    this.modalContent = page.locator('.modal-content');
    this.credentialModal = page.locator('.credential-modal');
    this.credentialModalContent = page.locator('.credential-modal-content');
    this.copyClientSecret = page.getByTitle('Copy client secret');
    this.copyClientId = page.getByTitle('Copy client id');

    this.editIcon = page.locator('#edit-icon');
    this.cancelButton = page.locator('#cancel-button');
  }

  // Navigates from the app to the User Profile page's Federation tokens tab.
  public async open(): Promise<void> {
    await this.page.locator('a:text("User Profile")').click();
    await this.page.getByText('Federation tokens').click();
  }

  // The name cell for a named credential.
  public nameCell(name: string): Locator {
    return this.page.locator(`div[id="${name}-name-cell"]`);
  }

  // The actions cell for a named credential.
  public actionsCell(name: string): Locator {
    return this.page.locator(`div[id="${name}-actions-cell"]`);
  }

  // The delete (confirm) button for a named credential.
  public deleteButton(name: string): Locator {
    return this.page.locator(`#${name}-delete-credential-button`);
  }

  // The delete confirm-button custom element for a named credential.
  public deleteConfirmButton(name: string): Locator {
    return this.page.locator(`gpf-confirm-button[id="${name}-delete-credential-button"]`);
  }

  // The rename input for a named credential.
  public newNameInput(name: string): Locator {
    return this.page.locator(`#${name}-new-name-input`);
  }
}
