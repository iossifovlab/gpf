import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';
import { loginLiteralAdmin, LITERAL_ADMIN_EMAIL } from './_literal_admin';
import { UserManagementPage } from './pages/user-management.page';
import { Login } from './components/login.component';
import { Header } from './components/header.component';
import { DescriptionEditor } from './components/description-editor.component';
import { Datasets } from './components/datasets.component';
import { PhenoBrowser } from './components/pheno-browser.component';

// tb-nxl: this is the only spec file allowed to import _literal_admin.
// Jenkinsfile.e2e enforces this with a CI grep step. All other specs
// must use utils.loginWorkerUser() — the per-worker pool that breaks
// admin-row sharing across parallel workers.
//
// File-level serial mode: every test here writes to /management or
// asserts on shared admin/group/dataset state. Two .serial describes
// in the same file would still fan out across workers under
// fullyParallel: true, so we configure the whole file as serial — all
// tests run sequentially on a single worker. Slow but correct; the
// alternative (cross-describe admin-row writes) is what tb-nxl exists
// to prevent.
test.describe.configure({ mode: 'serial' });

test.describe('Management tests for reset password in Users', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
  });

  test('should reset password', async({ page }) => {
    const um = new UserManagementPage(page);
    const login = new Login(page);
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await navigateToManagement(page);
    await utils.createUser(page, email, username);

    await expect(um.passwordCell(email)).toBeEmpty();

    await um.resetPasswordButton(email).locator('button').click();
    await um.resetConfirm.click();

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await login.newPassword1.fill(password);
    await login.newPassword2.fill(password);
    await login.loginButton.click();

    await page.waitForSelector('gpf-home');
    await expect(login.logOutButton).toBeVisible();
    await login.logOutButton.click();
  });

  test('should reset password when login', async({ page }) => {
    const login = new Login(page);
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await navigateToManagement(page);
    await utils.createUser(page, email, username);

    const logoutResponse = page.waitForResponse(resp => resp.url().includes('logout') && resp.status() === 204);
    await login.logOutButton.click();
    await logoutResponse;

    await login.logInButton.click();
    await login.forgottenPassword.click();
    await login.emailInput.fill(email);
    await login.resetPasswordText.click();

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await login.newPassword1.fill(password);
    await login.newPassword2.fill(password);
    await login.resetPasswordText.click();
    await utils.login(page, email, password);

    await expect(login.logOutButton).toBeVisible();
    await login.logOutButton.click();
  });
});

test.describe('Users management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await navigateToManagement(page);
  });
  test('should not create user with already used email', async({ page }) => {
    const um = new UserManagementPage(page);
    await utils.createUser(page, 'used_email@email.com', 'used_name');

    await um.createUserFormButton.click();

    await um.createContainer.locator('#name-box').fill('used_name');
    await um.createContainer.locator('#email-box').fill('used_email@email.com');
    await um.createUserButton.click();

    await expect(page.getByText(' Error: wdae user with this email already exists. ')).toBeVisible();
    await deleteUser(page, 'used_email@email.com');
  });

  test('should not create user with no email or name', async({ page }) => {
    const um = new UserManagementPage(page);
    await um.createUserFormButton.click();

    await um.createContainer.locator('#name-box').fill('no_username');
    await um.createUserButton.click();
    await expect(um.emailBox).toBeFocused();

    await um.nameBox.clear();
    await um.createContainer.locator('#email-box').fill('no_username_email@email.com');
    await um.createUserButton.click();
    await expect(um.nameBox).toBeFocused();

    await expect(page.getByText('div:id("no_username_email@email.com-user-cell")')).not.toBeVisible();
  });

  test('should not create user with invalid email or name', async({ page }) => {
    const um = new UserManagementPage(page);
    await um.createUserFormButton.click();

    await um.createContainer.locator('#name-box').fill('valid_test_name');
    await um.createContainer.locator('#email-box').fill('invalid_email@email.c');
    await um.createUserButton.click();
    await expect(um.emailBox).toBeFocused();

    await um.emailBox.clear();
    await um.createContainer.locator('#email-box').fill('invalid_email@');
    await um.createUserButton.click();
    await expect(um.emailBox).toBeFocused();

    await um.emailBox.clear();
    await um.createContainer.locator('#email-box').fill('invalid_email');
    await um.createUserButton.click();
    await expect(um.emailBox).toBeFocused();

    await um.nameBox.clear();
    await um.createContainer.locator('#email-box').fill('invalid_email@email.com');
    await um.createContainer.locator('#name-box').fill('va');
    await um.createUserButton.click();
    await expect(um.nameBox).toBeFocused();
  });

  test('should search and find user', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await searchInTable(page, username);
    await expect(um.userCell(email)).toBeVisible();

    await searchInTable(page, email);
    await expect(um.userCell(email)).toBeVisible();
  });

  test('should search and not find user', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await searchInTable(page, username);
    await expect(um.userCell(email)).not.toBeVisible();

    await searchInTable(page, email);
    await expect(um.userCell(email)).not.toBeVisible();
  });

  test('should edit username', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await um.userCell(email).getByTitle('Edit').click();
    await um.newNameInput(email).focus();
    await page.keyboard.type('123');
    await page.keyboard.press('Enter');

    await expect(um.userCell(email)).toContainText(username+'123');
  });

  test('should try to delete username', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await um.userCell(email).getByTitle('Edit').click();
    await um.newNameInput(email).clear();
    await page.keyboard.press('Enter');
    await expect(um.newNameInput(email)).toBeFocused();
    await um.cancelButton.click();

    await expect(um.userCell(email)).toContainText(username);
  });

  test('should cancel the process of creating user', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await um.createUserFormButton.click();

    await um.createContainer.locator('#name-box').fill(username);
    await um.createContainer.locator('#email-box').fill(email);
    await um.cancelUserCreationButton.click();

    await expect(um.userCell(email)).not.toBeVisible();
  });

  test('should check admin', async({ page }) => {
    const um = new UserManagementPage(page);
    await searchInTable(page, 'admin@iossifovlab.com');
    await expect(page.locator('#admin-list-item gpf-confirm-button')).not.toBeVisible();
    await expect(um.datasetsCell('admin@iossifovlab.com'))
      .toHaveText(
        'ALL Genotypes' +
        'COMP Genotypes' +
        'Hello World Genotypes' +
        'comp_all_liftover' +
        'comp_denovo_liftover' +
        'comp_vcf_liftover' +
        'denovo_helloworld' +
        'iossifov_2014_liftover' +
        'multi_liftover' +
        'pheno_helloworld' +
        'vcf_helloworld'
      );
    await expect(um.resetPasswordButton('admin@iossifovlab.com')).toBeVisible();
    await expect(page.locator('[id="admin@iossifovlab.com-reset-delete-user-button"]')).not.toBeVisible();
  });

  test('should add and remove group', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await um.addButtonIn(um.groupsCell(email)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, 'denovo_helloworld');
    await page.waitForSelector('button:text("denovo_helloworld")');
    await um.menuItem('denovo_helloworld').click();

    await expect(um.groupsCell(email)).toContainText(email);
    await expect(um.groupsCell(email)).toContainText('any_user');
    await expect(um.groupsCell(email)).toContainText('denovo_helloworld');
    await expect(um.datasetsCell(email)).toContainText('denovo_helloworld');

    await um.listItemConfirm(um.groupsCell(email), 'denovo_helloworld').click();
    await um.removeConfirm.click();

    await expect(um.groupsCell(email)).not.toContainText('denovo_helloworld');
    await expect(um.datasetsCell(email)).not.toContainText('denovo_helloworld');
  });
});

test.describe('Groups management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await new UserManagementPage(page).navLink('Management').click();
  });

  test('should create and delete group with user and dataset', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    // add user
    await addUserToGroup(page, groupName, email);
    await expect(um.usersCell(groupName)).toContainText(email);
    await expect(page.getByText('Empty groups with no users or datasets will be deleted!')).not.toBeVisible();

    // add dataset
    await addDatasetToGroup(page, groupName, 'iossifov_2014_liftover');

    // check if the group is added
    await page.reload();
    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(um.groupCell(groupName)).toBeVisible();

    await deleteGroup(page, groupName);
    await deleteUser(page, email);
  });

  test('should create and delete group with user only', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    // add user
    await addUserToGroup(page, groupName, email);
    await expect(um.usersCell(groupName)).toContainText(email);
    await expect(page.getByText('Empty groups with no users or datasets will be deleted!')).not.toBeVisible();

    // check if the group is added
    await page.reload();
    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(um.groupCell(groupName)).toBeVisible();

    await deleteGroup(page, groupName);
    await deleteUser(page, email);
  });

  test('should create and delete group with dataset only', async({ page }) => {
    const um = new UserManagementPage(page);
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    await addDatasetToGroup(page, groupName, 'iossifov_2014_liftover');
    await expect(um.datasetsCell(groupName)).toContainText('iossifov_2014_liftover');

    // check if the group is added
    await page.reload();
    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(um.groupCell(groupName)).toBeVisible();

    await deleteGroup(page, groupName);
  });

  test('should not create with no users or datasets', async({ page }) => {
    const um = new UserManagementPage(page);
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    await page.reload();
    await um.navLink('Groups').click();
    await expect(um.groupCell(groupName)).not.toBeVisible();
  });

  test('should not create group with invalid name', async({ page }) => {
    const um = new UserManagementPage(page);
    await um.navLink('Groups').click();
    await um.createGroupFormButton.click();

    await um.groupNameBox.fill('c');
    await um.createGroupButton.click();
    await expect(um.groupNameBox).toBeFocused();

    await um.groupNameBox.clear();
    await um.groupNameBox.fill('cc');
    await um.createGroupButton.click();
    await expect(um.groupNameBox).toBeFocused();

    await um.cancelGroupCreationButton.click();
  });

  test('should cancel the process of creating group', async({ page }) => {
    const um = new UserManagementPage(page);
    await um.navLink('Groups').click();

    await um.createGroupFormButton.click();
    await um.groupNameBox.fill('cancel_creation_group');
    await um.cancelGroupCreationButton.click();
    await expect(um.groupCell('cancel_creation_group')).not.toBeVisible();
  });

  test('should fail to create group with already used name', async({ page }) => {
    const um = new UserManagementPage(page);
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    // add dataset to make the group valid
    await addDatasetToGroup(page, groupName, 'iossifov_2014_liftover');
    await expect(um.datasetsCell(groupName)).toContainText('iossifov_2014_liftover');

    await um.createGroupFormButton.click();
    await um.groupNameBox.fill(groupName);
    await um.createGroupButton.click();
    await expect(page.getByText(` '${groupName}' already exists choose another name! `)).toBeVisible();
  });

  test('should add and remove user and dataset from Group', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    const datasetName = 'iossifov_2014_liftover';

    await addUserToGroup(page, groupName, email);
    await addDatasetToGroup(page, groupName, datasetName);

    // remove user
    await searchInTable(page, groupName);
    await um.listItemConfirm(um.usersCell(groupName), email).click();
    await um.removeConfirm.click();
    await expect(um.usersCell(groupName)).not.toContainText(email);

    // remove dataset
    await um.listItemConfirm(um.datasetsCell(groupName), datasetName).click();
    await um.removeConfirm.click();
    await expect(um.datasetsCell(groupName)).not.toContainText(datasetName);

    await expect(page.getByText('Empty groups with no users or datasets will be deleted!')).toBeVisible();
    await page.reload();
    await um.navLink('Groups').click();
    await expect(um.groupCell(groupName)).not.toBeVisible();

    await deleteUser(page, email);
  });

  test('should add and remove users and groups from Users and Groups', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'iossifov_2014_liftover';

    const groupName1 = utils.getRandomString();
    await createGroup(page, groupName1);
    await addUserToGroup(page, groupName1, email);
    await addDatasetToGroup(page, groupName1, datasetName);

    const groupName2 = utils.getRandomString();
    await createGroup(page, groupName2);
    await addDatasetToGroup(page, groupName2, datasetName);

    // check if the user has the new group
    await um.navLink('Users').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(um.groupsCell(email)).toContainText(groupName1);

    // add the second group to the user in Users
    await um.addButtonIn(um.groupsCell(email)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName2);
    await page.waitForSelector(`button:text("${groupName2}")`);
    await um.menuItem(groupName2).click();
    await expect(um.groupsCell(email)).toContainText(groupName2);

    // go and check users list of the second group in Groups
    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName2);
    await expect(um.usersCell(groupName2)).toContainText(email);

    // delete both groups
    await deleteGroup(page, groupName1);
    await deleteGroup(page, groupName2);

    // check groups list of the user
    await um.navLink('Users').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(um.groupsCell(email)).not.toContainText(groupName1);
    await expect(um.groupsCell(email)).not.toContainText(groupName2);

    await deleteUser(page, email);
  });

  test('should check if new groups and any_user group when creating user', async({ page }) => {
    const um = new UserManagementPage(page);
    const username1 = utils.getRandomString();
    const email1 = `${username1}@mail.com`;
    await utils.createUser(page, email1, username1);

    const username2 = utils.getRandomString();
    const email2 = `${username2}@mail.com`;
    await utils.createUser(page, email2, username2);

    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, email1);
    await expect(um.groupCell(email1)).toBeVisible();
    await searchInTable(page, email2);
    await expect(um.groupCell(email2)).toBeVisible();

    await searchInTable(page, 'any_user');
    await expect(um.usersCell('any_user')).toContainText(email1);
    await expect(um.usersCell('any_user')).toContainText(email2);

    await deleteUser(page, email1);
    await deleteUser(page, email2);

    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, email1);
    await expect(um.groupCell(email1)).not.toBeVisible();
    await searchInTable(page, email2);
    await expect(um.groupCell(email2)).not.toBeVisible();

    await searchInTable(page, 'any_user');
    await expect(um.usersCell('any_user')).not.toContainText(email1);
    await expect(um.usersCell('any_user')).not.toContainText(email2);
  });

  test('should check if the new group is deleted after removing it in Users', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    await um.navLink('Users').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await um.listItemConfirm(um.groupsCell(email), groupName).click();
    await um.removeConfirm.click();
    await expect(um.listItem(um.groupsCell(email), groupName)).not.toBeVisible();

    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(um.groupCell(groupName)).not.toBeVisible();

    await deleteUser(page, email);
  });

  test('should check if the new group is deleted after deleting the user', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    await deleteUser(page, email);

    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(um.groupCell(groupName)).not.toBeVisible();
  });
});

test.describe('Datasets management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await navigateToManagement(page);
  });

  test('should add group to user and check data in Datasets', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = 'vcf_helloworld';

    // add group to user
    await um.addButtonIn(um.groupsCell(email)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName);
    await page.waitForSelector(`button:text("${groupName}")`);
    await um.menuItem(groupName).click();

    // check datasets of the user
    await expect(um.datasetsCell(email)).toContainText(groupName);

    // check dataset in Datasets
    await um.datasetsTab().click();
    await expect(um.usersListCell(groupName)).toContainText(username);
    await expect(um.usersListCell(groupName)).toContainText(email);

    await deleteUser(page, email);

    await um.datasetsTab().click();
    await expect(um.usersListCell(groupName)).not.toContainText(username);
    await expect(um.usersListCell(groupName)).not.toContainText(email);
  });

  test('should create group, add datasets and check data in Datasets', async({ page }) => {
    const um = new UserManagementPage(page);
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    const datasetName1 = 'iossifov_2014_liftover';
    const datasetName2 = 'vcf_helloworld';
    await addDatasetToGroup(page, groupName, datasetName1);
    await addDatasetToGroup(page, groupName, datasetName2);

    await um.datasetsTab().click();
    await expect(um.groupsCell(datasetName1)).toContainText('any_dataset');
    await expect(um.groupsCell(datasetName1)).toContainText(datasetName1);
    await expect(um.groupsCell(datasetName1)).toContainText(groupName);
    await expect(um.groupsCell(datasetName2)).toContainText('any_dataset');
    await expect(um.groupsCell(datasetName2)).toContainText(datasetName2);
    await expect(um.groupsCell(datasetName2)).toContainText(groupName);

    await deleteGroup(page, groupName);

    await expect(async() => {
      await um.datasetsTab().click();
      await expect(um.groupsCell(datasetName1)).not.toContainText(groupName);
      await expect(um.groupsCell(datasetName2)).not.toContainText(groupName);
    }).toPass({intervals: [1000]});
  });

  test('should create group, add dataset and users and check data in Datasets', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'iossifov_2014_liftover';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);
    await addDatasetToGroup(page, groupName, datasetName);

    // check datasets of the user
    await um.navLink('Users').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(um.datasetsCell(email)).toContainText(datasetName);

    // check dataset in Datasets
    await um.datasetsTab().click();
    await expect(um.usersCell(datasetName)).toContainText(username);
    await expect(um.usersCell(datasetName)).toContainText(email);
    await expect(um.groupsCell(datasetName)).toContainText(groupName);

    // remove dataset from the group
    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await um.listItemConfirm(um.datasetsCell(groupName), datasetName).click();
    await um.removeConfirm.click();
    await expect(um.listItem(um.datasetsCell(groupName), datasetName)).not.toBeVisible();

    await um.datasetsTab().click();
    await expect(um.groupsCell(datasetName)).not.toContainText(groupName);

    await deleteUser(page, email);

    await um.datasetsTab().click();
    await expect(um.usersCell(datasetName)).not.toContainText(username);
    await expect(um.usersCell(datasetName)).not.toContainText(email);
  });

  test('should add and remove groups in Datasets', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'vcf_helloworld';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    // add the group to dataset in Datasets
    await um.datasetsTab().click();
    await um.addButtonIn(um.groupsCell(datasetName)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName);
    await page.waitForSelector(`button:text("${groupName}")`);
    await um.menuItem(groupName).click();

    // check users list of dataset
    await expect(um.usersCell(datasetName)).toContainText(username);
    await expect(um.usersCell(datasetName)).toContainText(email);

    // check group list of dataset
    await expect(um.groupsCell(datasetName)).toContainText(groupName);

    // remove the group from the dataset
    await um.datasetsTab().click();
    await um.listItemConfirm(um.groupsCell(datasetName), groupName).click();
    await um.removeConfirm.click();
    // tb-pa6: drop the meaningless `${groupName}-datasets-cell` assertion
    // (only renders on the Groups tab; not.toBeVisible() against a
    // non-existent locator passes trivially). Lines below verify the
    // removal correctly via the `${datasetName}-groups-cell`
    // (Datasets-tab) locator.
    await expect(um.groupsCell(datasetName)).not.toContainText(groupName);
    await expect(um.usersCell(datasetName)).not.toContainText(email);
    await expect(um.usersCell(datasetName)).not.toContainText(username);
  });

  test('should add groups with user to dataset and delete the user', async({ page }) => {
    const um = new UserManagementPage(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'denovo_helloworld';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    // add the group to dataset in Datasets
    await um.datasetsTab().click();
    await um.addButtonIn(um.groupsCell(datasetName)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName);
    await page.waitForSelector(`button:text("${groupName}")`);
    await um.menuItem(groupName).click();

    // check users list of dataset
    await expect(um.usersCell(datasetName)).toContainText(username);
    await expect(um.usersCell(datasetName)).toContainText(email);

    // check group list of dataset
    await expect(um.groupsCell(datasetName)).toContainText(groupName);

    // check dataset cell of the user in Users
    await um.navLink('Users').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(um.datasetsCell(email)).toContainText(datasetName);

    await deleteUser(page, email);

    // check the group in Groups
    await um.navLink('Groups').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(um.usersCell(groupName)).not.toContainText(email);
    await expect(um.datasetsCell(groupName)).not.toContainText(email);

    await um.datasetsTab().click();
    await expect(um.groupsCell(datasetName)).toContainText(groupName);
    await expect(um.usersCell(datasetName)).not.toContainText(email);
    await expect(um.usersCell(datasetName)).not.toContainText(username);
  });
});

// tb-nxl: tests folded in from app.spec.ts. These need the admin group
// (Management nav button visibility, /management write-throughs) and
// so go through loginLiteralAdmin. Kept as a separate describe block
// so the origin is visible; runs serial under the file-level config.
test.describe('Admin surface (folded from app.spec.ts, tb-nxl)', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
  });

  test('should click on the "Management" button and navigate to "/management"', async({ page }) => {
    const um = new UserManagementPage(page);
    const managementUrl = `${utils.frontendUrl}/management`;

    await loginLiteralAdmin(page);

    await um.navLink('Management').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(managementUrl);
  });

  test(`should check navigation bar for the right elements for ${LITERAL_ADMIN_EMAIL} user`, async({ page }) => {
    const header = new Header(page);
    await loginLiteralAdmin(page);

    const navigationTabs = ['Home', 'Datasets', 'Gene profiles', 'User profile', 'Management', 'About'];
    await expect(header.navLinks).toHaveCount(navigationTabs.length);

    for (const tab of navigationTabs) {
      await expect(header.navLinkByText(tab)).toBeVisible();
    }
  });

  test('should login admin and give user access rights for Hello World Genotypes, ' +
       'then login user and verify his rights', async({ page }) => {
    const um = new UserManagementPage(page);
    const datasets = new Datasets(page);
    const login = new Login(page);
    const newUserPasswordSuffix = '!!__3456';
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await um.navLink('Management').click();
    await utils.createUser(page, email, username);

    await um.addButtonIn(um.groupsCell(email)).click();
    await um.searchMenuTextbox.focus();
    await page.keyboard.type('helloworld_genotypes');
    await um.addItemButton.filter({ hasText: 'helloworld_genotypes' }).click();
    await expect(um.passwordCell(email)).toBeEmpty();

    await um.resetPasswordButton(email).locator('button').click();
    await um.resetConfirm.click();
    await utils.logout(page);

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await login.newPassword1.fill('secret' + newUserPasswordSuffix);
    await login.newPassword2.fill('secret' + newUserPasswordSuffix);
    await login.resetPasswordInput.click();
    await expect(page).toHaveURL(`${utils.frontendUrl}/home`);

    await utils.login(page, email, 'secret' + newUserPasswordSuffix);

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    await expect(datasets.registerAlert).toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    await expect(datasets.registerAlert).toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    await expect(datasets.registerAlert).toBeVisible();
  });

  test('should login admin and give user access rights for ALL Genotypes, ' +
     'then login user and verify his rights', async({ page }) => {
    const um = new UserManagementPage(page);
    const datasets = new Datasets(page);
    const login = new Login(page);
    const newUserPasswordSuffix = '!!__3456';
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await um.navLink('Management').click();
    await utils.createUser(page, email, username);

    await um.addButtonIn(um.groupsCell(email)).click();
    await um.searchMenuTextbox.fill('ALL_genotypes');
    await page.getByRole('button', { name: 'ALL_genotypes', exact: true }).click();
    await expect(um.passwordCell(email)).toBeEmpty();

    await um.resetPasswordButton(email).locator('button').click();
    await um.resetConfirm.click();
    await utils.logout(page);

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await login.newPassword1.fill('secret' + newUserPasswordSuffix);
    await login.newPassword2.fill('secret' + newUserPasswordSuffix);
    await login.resetPasswordInput.click();

    await expect(page).toHaveURL(`${utils.frontendUrl}/home`);

    await utils.login(page, email, 'secret' + newUserPasswordSuffix);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    await expect(datasets.registerAlert).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    await expect(datasets.registerAlert).toBeVisible();
  });
});

// tb-nxl-fix: tests folded in from datasets.spec.ts. The four
// "Access rights and icons" tests below click `a:text("Management")`
// after admin login and write group memberships on shared rows
// (vcf_helloworld / pheno_helloworld dataset rows; research@
// user row). Build #28 of gpf-web-e2e showed them failing under
// loginWorkerUser (worker users have no admin group, so the
// Management nav link doesn't render). Moving them here puts them
// on the file-level serial worker that already owns all literal-
// admin /management writes — no parallel admin-row contention.
test.describe('Datasets access rights via Management '
  + '(folded from datasets.spec.ts, tb-nxl-fix)', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    // The migrated tests below open with `utils.logout(page)` to assert
    // the unauthenticated UI surface — that only works if beforeEach
    // leaves the page logged in. Original datasets.spec.ts shape
    // (loginWorkerUser was admin pre-tb-nxl).
    await loginLiteralAdmin(page);
  });

  test('should give rights for vcf_helloworld to any_user', async({ page }) => {
    const um = new UserManagementPage(page);
    const header = new Header(page);
    // check if Genotype browser is disabled when no user is logged in
    await utils.logout(page);
    const study = utils.datasetIds.vcfHelloWorld;
    const group = 'any_user';
    await utils.navigateToDataset(page, study);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item disabled-tool');

    // add any_user group to study
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await um.datasetsTab().click();
    await searchInTable(page, study);

    await um.addButtonIn(um.groupsCell(study)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, group);
    await page.waitForSelector(`button:text("${group}")`);
    await um.menuItem(group).click();

    await expect(um.groupsCell(study)).toContainText(group);

    // check if Genotype browser is enabled when no user is logged in
    await utils.logout(page);

    await utils.navigateToDataset(page, study);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item');

    // remove any_user from list of groups of the study
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await um.datasetsTab().click();
    await searchInTable(page, study);
    await um.listItemConfirm(um.groupsCell(study), group).click();
    await um.removeConfirm.click();
    // tb-pa6: assert against the locator visible on the Datasets tab
    // (where this test sits). The previous assertion targeted
    // `${group}-datasets-cell` which only renders on the Groups tab —
    // .not.toBeVisible() against a never-rendered locator passes
    // trivially, leaving an actually-failed Remove click silent.
    await expect(um.listItem(um.groupsCell(study), group)).not.toBeVisible();
  });

  test('should give rights for vcf_helloworld to researcher', async({ page }) => {
    const um = new UserManagementPage(page);
    const header = new Header(page);
    // check if Genotype browser is disabled when no user is logged in
    await utils.logout(page);

    const study = utils.datasetIds.vcfHelloWorld;
    await utils.navigateToDataset(page, study);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item disabled-tool');

    // add group to reasearcher
    const researcher = 'research@iossifovlab.com';
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await searchInTable(page, researcher);

    await um.addButtonIn(um.groupsCell(researcher)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, study);
    await page.waitForSelector(`button:text("${study}")`);
    await um.menuItem(study).click();

    await utils.logout(page);
    // check if Genotype browser is enabled when researcher is logged in
    await utils.login(page, researcher, 'secret');

    await utils.navigateToDataset(page, study);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(header.toolNavItem('Genotype Browser')).toHaveClass('nav-item');

    // remove group from groups list of research
    await utils.logout(page);
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await searchInTable(page, researcher);

    await um.listItemConfirm(um.groupsCell(researcher), study).click();
    await um.removeConfirm.click();

    await expect(um.groupsCell(researcher)).not.toContainText(study);
  });

  test('should give rights for pheno_helloworld to any_user', async({ page }) => {
    const um = new UserManagementPage(page);
    const datasets = new Datasets(page);
    const phenoBrowser = new PhenoBrowser(page);
    const study = utils.datasetIds.phenoHelloWorld;
    const group = 'any_user';

    // check if Phenotype browser download is disabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(datasets.phenoBrowser).toBeVisible();
    await expect(phenoBrowser.downloadMeasures).toContainClass('disabled-download');

    // add any_user group to pheno study
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await um.datasetsTab().click();
    await searchInTable(page, study);

    await um.addButtonIn(um.groupsCell(study)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, group);
    await page.waitForSelector(`button:text("${group}")`);
    await um.menuItem(group).click();

    await expect(um.groupsCell(study)).toContainText(group);

    // check if Phenotype browser is enabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(datasets.phenoBrowser).toBeVisible();
    await expect(phenoBrowser.downloadMeasures).not.toContainClass('disabled-download');

    // remove any_user from list of groups of the pheno study
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await um.datasetsTab().click();
    await searchInTable(page, study);
    await um.listItemConfirm(um.groupsCell(study), group).click();
    await um.removeConfirm.click();
    // tb-pa6: assert against the Datasets-tab locator (see twin fix
    // ~85 lines above for vcf_helloworld → any_user).
    await expect(um.listItem(um.groupsCell(study), group)).not.toBeVisible();
  });

  test('should give rights for pheno_helloworld to researcher', async({ page }) => {
    const um = new UserManagementPage(page);
    const datasets = new Datasets(page);
    const phenoBrowser = new PhenoBrowser(page);
    const study = utils.datasetIds.phenoHelloWorld;
    const researcher = 'research@iossifovlab.com';

    // check if Phenotype browser download is disabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(datasets.phenoBrowser).toBeVisible();
    await expect(phenoBrowser.downloadMeasures).toContainClass('disabled-download');

    // add pheno group to reasearcher
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await searchInTable(page, researcher);

    await um.addButtonIn(um.groupsCell(researcher)).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, study);
    await page.waitForSelector(`button:text("${study}")`);
    await um.menuItem(study).click();

    await utils.logout(page);
    // check if Phenotype browser download is enabled when researcher is logged in
    await utils.login(page, researcher, 'secret');

    await utils.navigateToDataset(page, study);
    await expect(datasets.phenoBrowser).toBeVisible();
    await expect(phenoBrowser.downloadMeasures).not.toContainClass('disabled-download');

    // remove pheno group from groups list of research
    await utils.logout(page);
    await loginLiteralAdmin(page);
    await um.navLink('Management').click();
    await searchInTable(page, researcher);

    await um.listItemConfirm(um.groupsCell(researcher), study).click();
    await um.removeConfirm.click();

    await expect(um.groupsCell(researcher)).not.toContainText(study);
  });
});

// tb-nxl-fix: folded in from datasets-description.spec.ts. The
// 'Dataset description tests' describe needs admin to see #edit-icon
// (and the #empty-description placeholder, which is the admin-only
// "write a description" prompt). Build #28 surfaced this as 'should
// display empty description placeholder text' failing under
// loginWorkerUser; the rest of the .serial describe was skipped.
// Moved as-is, with loginWorkerUser → loginLiteralAdmin.
test.describe('Dataset description (folded from datasets-description.spec.ts, '
  + 'tb-nxl-fix)', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Dataset description');
  });

  test('should display dataset description window', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.datasetDescription).toBeVisible();
  });

  test('should display empty description placeholder text', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.emptyDescription).toBeVisible();
    await expect(
      description.emptyDescription
    ).toHaveText('Empty description. Write a description using the pencil button to the right.');
  });

  test('should display edit icon', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.editIcon).toBeVisible();
  });

  test('should display angular markdown editor after clicking the edit button', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.editor).not.toBeVisible();
    await description.editIcon.click();
    await expect(description.editor).toBeVisible();
  });

  test('should display preview button', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.previewButton).not.toBeVisible();
    await description.editIcon.click();
    await expect(description.previewButton).toBeVisible();
  });

  test('should display save button', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.saveButton).not.toBeVisible();
    await description.editIcon.click();
    await expect(description.saveButton).toBeVisible();
  });

  test('should display close button', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.closeButton).not.toBeVisible();
    await description.editIcon.click();
    await expect(description.closeButton).toBeVisible();
  });

  test('should display the editor header bar', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.mdHeader).not.toBeVisible();
    await description.editIcon.click();
    await expect(description.mdHeader).toBeVisible();
  });

  test('should hide the edit button after clicking it', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.editIcon).toBeVisible();
    await description.editIcon.click();
    await expect(description.editIcon).not.toBeVisible();
    await description.closeButton.click();
    await expect(description.editIcon).toBeVisible();
  });

  test('should save the markdown', async({ page }) => {
    const description = new DescriptionEditor(page);
    await expect(description.emptyDescription).toBeVisible();
    await expect(description.markdownParagraph).not.toBeVisible();

    // The SPA's markdown-editor save() does an optimistic UI update + a
    // fire-and-forget POST to /datasets/description/<id>. Without waiting
    // for the response the page can be torn down before the POST reaches
    // the backend, leaving stale content for the next test run.
    const isDescriptionSave = (resp: import('@playwright/test').Response): boolean =>
      resp.url().includes('/api/v3/datasets/description/') && resp.request().method() === 'POST';

    await description.editIcon.click();
    await description.editorTextarea.type('TEST DESCRIPTION ASDF');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      description.saveButton.click(),
    ]);
    await expect(description.markdownParagraph).toHaveText('TEST DESCRIPTION ASDF');
    await expect(description.emptyDescription).not.toBeVisible();

    await description.editIcon.click();
    await description.editorTextarea.fill('');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      description.saveButton.click(),
    ]);
    await expect(description.emptyDescription).toBeVisible();
  });
});

// tb-nxl-fix: folded in from datasets-description.spec.ts ":146" — the
// admin Management write that grants user_iossifov_2014@iossifovlab.com
// access to iossifov_2014_liftover, then writes a description, then
// reverts. Needs admin (Management nav) and serial coexistence with
// other admin Management writes.
test.describe('Dataset description access rights '
  + '(folded from datasets-description.spec.ts, tb-nxl-fix)', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
  });

  test('should log admin, give researcher user access rights for iossifov_2014,' +
       'create dataset description for iossifov_2014, log researcher user and check ' +
       'whether the newly created description exists and that it cannot be edited', async({ page }) => {
    const um = new UserManagementPage(page);
    const header = new Header(page);
    const description = new DescriptionEditor(page);
    await um.navLink('Management').click();

    // gpf#962: under CI load the Users table renders only a prefix of the
    // user list, so the last-sorted rows (this user) can be absent for
    // >20s and the Add-button click times out. Filter the table down to
    // the target user first so its row is guaranteed to be present.
    await searchInTable(page, 'user_iossifov_2014@iossifovlab.com');
    await um.addButtonIn(um.groupsCell('user_iossifov_2014@iossifovlab.com')).click();
    await page.waitForSelector('.add-item-button');
    await um.searchMenuTextbox.focus();
    await page.keyboard.type('iossifov_2014_liftover');
    await page.waitForSelector('button:text("iossifov_2014_liftover")');
    await um.menuItem('iossifov_2014_liftover').click();
    await page.mouse.click(0, 0); // close the menu

    await header.navLink('Datasets').click();
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');

    // tb-pa6: same fire-and-forget POST race as the in-file
    // `should save the markdown` test (line 1135). The SPA's
    // markdown-editor save() does an optimistic UI update + a
    // POST to /datasets/description/<id> without awaiting the
    // response. Without waiting here, the test logs out and the
    // researcher logs in before the save reaches the backend —
    // researcher's GET sees an empty description and the
    // toHaveText assertion at line 1200 times out.
    const isDescriptionSave = (resp: import('@playwright/test').Response): boolean =>
      resp.url().includes('/api/v3/datasets/description/') && resp.request().method() === 'POST';

    await description.editIcon.click();
    await description.editorTextarea.fill('IOSSIFOV TEST DESCRIPTION');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      description.saveButton.click(),
    ]);
    await utils.logout(page);

    await utils.login(page, 'user_iossifov_2014@iossifovlab.com');
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    await expect(description.markdownParagraph).toHaveText('IOSSIFOV TEST DESCRIPTION');
    await expect(description.editIcon).not.toBeVisible();
    await utils.logout(page);

    await loginLiteralAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    // tb-pa6: assert the description is loaded before opening the
    // editor. Clicking #edit-icon before the GET completes leaves
    // markdown-editor's initialMarkdown empty, which makes the
    // subsequent fill('') + Save a no-op (markdown===initialMarkdown,
    // writeEvent never emitted, POST never fires, waitForResponse
    // times out).
    await expect(description.markdownParagraph).toHaveText('IOSSIFOV TEST DESCRIPTION');
    await description.editIcon.click();
    await description.editorTextarea.fill('');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      description.saveButton.click(),
    ]);

    await um.navLink('Management').click();
    // gpf#962: filter to the target user (see the grant step above) so the
    // row is present under CI load before interacting with its groups-cell.
    await searchInTable(page, 'user_iossifov_2014@iossifovlab.com');
    await um.listItemConfirm(
      um.groupsCell('user_iossifov_2014@iossifovlab.com'), 'iossifov_2014_liftover'
    ).click();
    await um.removeConfirm.click();
    await expect(
      um.groupsCell('user_iossifov_2014@iossifovlab.com')
    ).not.toContainText('iossifov_2014_liftover');
  });
});

// tb-nxl-fix: folded in from home-page.spec.ts. The 'Home page
// description tests' describe writes the global instance description
// (admin-only #edit-icon). Build #28 surfaced this as 'should add
// description' failing under loginWorkerUser. Moved as-is, with
// loginWorkerUser → loginLiteralAdmin.
test.describe('Home page description '
  + '(folded from home-page.spec.ts, tb-nxl-fix)', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(`${utils.frontendUrl}/home`, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await page.waitForSelector('gpf-home');
  });

  test('should add description', async({ page }) => {
    const description = new DescriptionEditor(page);
    await description.editIcon.click();
    await expect(description.editor).toBeVisible();
    await description.markdownEditorTextarea.fill('Test description');
    await description.saveButton.click();

    await expect(description.editor).not.toBeVisible();
    await page.reload();
    await expect(description.editContainerParagraph).toHaveText('Test description');

    await description.editIcon.click();
    await description.markdownEditorTextarea.clear();

    await description.saveButton.click();
    await expect(description.emptyDescription).toBeVisible();
  });

  test('should check if editing description is disabled when no access rights', async({ page }) => {
    const description = new DescriptionEditor(page);
    await description.editIcon.click();
    await description.markdownEditorTextarea.fill('Test description');
    await description.saveButton.click();


    await utils.logout(page);
    await page.waitForSelector('gpf-home');
    await expect(description.editContainerParagraph).toHaveText('Test description');
    await expect(description.editIcon).not.toBeVisible();

    await loginLiteralAdmin(page);
    await page.waitForSelector('gpf-home');

    await description.editIcon.click();
    await description.markdownEditorTextarea.clear();

    await description.saveButton.click();
    await expect(description.emptyDescription).toBeVisible();

    await utils.logout(page);
    await page.waitForSelector('gpf-home');
    await expect(description.markdownEditor).not.toBeVisible();
  });
});

async function createGroup(page: Page, name: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.navLink('Groups').click();
  await um.createGroupFormButton.click();
  await um.groupNameBox.fill(name);
  await um.createGroupButton.click();
  await expect(page.getByText(`${name}Empty groups with no users or datasets will be deleted!`)).toBeVisible();
}

async function deleteGroup(page: Page, name: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.navLink('Groups').click();
  await page.waitForSelector('gpf-groups-table');
  await searchInTable(page, name);
  await um.deleteGroupButton(name).click();

  const permissionResponse = page.waitForResponse(resp =>
    (resp.url().includes('revoke-permission') && resp.status() === 200)
    || (resp.url().includes('remove-user') && resp.status() === 204)
  );
  await um.deleteConfirm.click();
  await permissionResponse;

  await expect(um.groupCell(name)).not.toBeVisible();
}

async function addUserToGroup(page: Page, groupName: string, email: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.addButtonIn(um.usersCell(groupName)).click();
  await page.waitForSelector('.add-item-button');
  await searchInMenu(page, email);
  await page.waitForSelector(`button:text("${email}")`);
  await um.menuItem(email).click();
  await page.mouse.click(0, 0); // close the menu
  await expect(um.usersCell(groupName)).toContainText(email);
}

async function addDatasetToGroup(page: Page, groupName: string, datasetName: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.addButtonIn(um.datasetsCell(groupName)).click();
  await page.waitForSelector('.add-item-button');
  await searchInMenu(page, datasetName);
  await page.waitForSelector(`button:text("${datasetName}")`);
  await um.menuItem(datasetName).click();
  await page.mouse.click(0, 0); // close the menu
  await expect(um.datasetsCell(groupName)).toContainText(datasetName);
}

async function deleteUser(page: Page, email: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.navLink('Users').click();
  await page.waitForSelector('gpf-users-table');
  await searchInTable(page, email);
  await um.deleteUserButton(email).click();

  const deleteResponse = page.waitForResponse(
    resp => resp.request().method() === 'DELETE' && resp.status() === 204
  );
  await um.deleteConfirm.click();
  await deleteResponse;
}

async function searchInTable(page: Page, name: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.searchField.clear();
  await um.searchField.focus();
  await page.keyboard.type(name);
}

async function searchInMenu(page: Page, name: string): Promise<void> {
  const um = new UserManagementPage(page);
  await um.searchMenuTextbox.clear();
  await um.searchMenuTextbox.focus();
  await page.keyboard.type(name);
}

async function navigateToManagement(page: Page): Promise<void> {
  const um = new UserManagementPage(page);
  await um.navLink('Management').click();
  await page.waitForSelector('.grid-cell');
}
