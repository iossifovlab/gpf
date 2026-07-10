import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { FederationCredentials } from './components/federation-credentials.component';

test.describe('Federation token tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await new FederationCredentials(page).open();
  });

  test('should check federation tokens tab elements', async({ page }) => {
    const federation = new FederationCredentials(page);
    await expect(federation.root).toBeVisible();
    await expect(federation.newCredentialNameBox).toBeVisible();
    await expect(federation.createCredentialButton).toBeVisible();
    await expect(federation.nameHeader).toBeVisible();
    await expect(federation.actionsHeader).toBeVisible();
  });

  test('should create new credential', async({ page }) => {
    const federation = new FederationCredentials(page);
    const credentialName = utils.getRandomString();
    await federation.gridContainer.waitFor();
    await federation.newCredentialNameBox.fill(credentialName);
    await federation.createCredentialButton.click();
    await expect(federation.modalContent).toBeVisible();
    await expect(federation.modalContent)
      .toContainText('Federation credentials are shown only once, copy before closing!');
    await expect(federation.copyClientSecret).toBeVisible();
    await expect(federation.copyClientId).toBeVisible();
    await expect(federation.credentialModalContent.nth(0)).not.toBeEmpty();
    await expect(federation.credentialModalContent.nth(1)).not.toBeEmpty();

    await page.mouse.click(0, 0); // close modal
    await expect(federation.modalContent).not.toBeVisible();

    await expect(federation.nameCell(credentialName)).toBeVisible();
    await expect(federation.actionsCell(credentialName)).toBeVisible();

    await federation.deleteConfirmButton(credentialName).click();
    await federation.deleteConfirm.click();
    await federation.nameCell(credentialName).waitFor({state: 'detached'});
  });

  test('should not create credential with invalid name', async({ page }) => {
    const federation = new FederationCredentials(page);
    await federation.gridContainer.waitFor();
    await federation.newCredentialNameBox.fill('a');
    await federation.createCredentialButton.click();
    await expect(page.getByText('Credential names must be at least 3 symbols long.')).toBeVisible();
    await expect(federation.newCredentialNameBox).toBeFocused();
    await expect(federation.nameCell('a')).not.toBeVisible();

    await federation.newCredentialNameBox.fill('b');
    await federation.createCredentialButton.click();
    await expect(page.getByText('Credential names must be at least 3 symbols long.')).toBeVisible();
    await expect(federation.newCredentialNameBox).toBeFocused();
    await expect(federation.nameCell('ab')).not.toBeVisible();
  });

  test('should not create credential with existing name', async({ page }) => {
    const federation = new FederationCredentials(page);
    await federation.gridContainer.waitFor();
    await federation.newCredentialNameBox.fill('ExistingCredential');
    await federation.createCredentialButton.click();

    await federation.credentialModal.waitFor();
    await page.mouse.click(0, 0); // close modal
    await expect(federation.nameCell('ExistingCredential')).toBeVisible();

    await federation.newCredentialNameBox.fill('ExistingCredential');
    await federation.createCredentialButton.click();
    await expect(page.getByText('Credential with such name already exists!')).toBeVisible();
    await expect(federation.newCredentialNameBox).toBeFocused();

    await federation.deleteButton('ExistingCredential').click();
    await federation.deleteConfirm.click();
    await expect(federation.nameCell('ExistingCredential')).not.toBeVisible();
  });

  test('should rename credential', async({ page }) => {
    const federation = new FederationCredentials(page);
    await federation.gridContainer.waitFor();
    await federation.newCredentialNameBox.fill('RenameCredential');
    await federation.createCredentialButton.click();

    await federation.credentialModal.waitFor();
    await page.mouse.click(0, 0); // close modal
    await expect(federation.nameCell('RenameCredential')).toBeVisible();

    await federation.nameCell('RenameCredential').locator('#edit-icon').click();
    await expect(federation.newNameInput('RenameCredential')).toBeVisible();
    await expect(federation.cancelButton).toBeVisible();

    await federation.newNameInput('RenameCredential').clear();
    await federation.newNameInput('RenameCredential').fill('NewNameCredential');
    await page.keyboard.press('Enter');

    await expect(federation.nameCell('RenameCredential')).not.toBeVisible();
    await expect(federation.nameCell('NewNameCredential')).toBeVisible();

    await federation.deleteButton('NewNameCredential').click();
    await federation.deleteConfirm.click();
    await expect(federation.nameCell('NewNameCredential')).not.toBeVisible();
  });

  test('should cancel renaming credential', async({ page }) => {
    const federation = new FederationCredentials(page);
    await federation.gridContainer.waitFor();
    await federation.newCredentialNameBox.fill('Credential');
    await federation.createCredentialButton.click();

    await federation.credentialModal.waitFor();
    await page.mouse.click(0, 0); // close modal
    await expect(federation.nameCell('Credential')).toBeVisible();

    await federation.nameCell('Credential').locator('#edit-icon').click();
    await federation.newNameInput('Credential').clear();
    await federation.newNameInput('Credential').fill('Credentialllll');
    await federation.cancelButton.click();

    await expect(federation.nameCell('Credentialllll')).not.toBeVisible();
    await expect(federation.nameCell('Credential')).toBeVisible();

    await federation.deleteButton('Credential').click();
    await federation.deleteConfirm.click();
    await expect(federation.nameCell('Credential')).not.toBeVisible();
  });
});
