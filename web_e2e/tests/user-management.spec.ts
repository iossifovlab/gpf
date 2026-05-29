import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';
import { loginLiteralAdmin, LITERAL_ADMIN_EMAIL } from './_literal_admin';

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
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await navigateToManagement(page);
    await utils.createUser(page, email, username);

    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill(password);
    await page.locator('#id_new_password2').fill(password);
    await page.locator('.login-button').click();

    await page.waitForSelector('gpf-home');
    await expect(page.locator('#log-out-button')).toBeVisible();
    await page.locator('#log-out-button').click();
  });

  test('should reset password when login', async({ page }) => {
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await navigateToManagement(page);
    await utils.createUser(page, email, username);

    const logoutResponse = page.waitForResponse(resp => resp.url().includes('logout') && resp.status() === 204);
    await page.locator('#log-out-button').click();
    await logoutResponse;

    await page.locator('#log-in-button').click();
    await page.locator('#forgotten-password').click();
    await page.locator('#id_email').fill(email);
    await page.getByText('Reset password').click();

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill(password);
    await page.locator('#id_new_password2').fill(password);
    await page.getByText('Reset password').click();
    await utils.login(page, email, password);

    await expect(page.locator('#log-out-button')).toBeVisible();
    await page.locator('#log-out-button').click();
  });
});

test.describe('Users management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await navigateToManagement(page);
  });
  test('should not create user with already used email', async({ page }) => {
    await utils.createUser(page, 'used_email@email.com', 'used_name');

    await page.locator('#create-user-form-button').click();

    await page.locator('.create-container').locator('#name-box').fill('used_name');
    await page.locator('.create-container').locator('#email-box').fill('used_email@email.com');
    await page.locator('#create-user-button').click();

    await expect(page.getByText(' Error: wdae user with this email already exists. ')).toBeVisible();
    await deleteUser(page, 'used_email@email.com');
  });

  test('should not create user with no email or name', async({ page }) => {
    await page.locator('#create-user-form-button').click();

    await page.locator('.create-container').locator('#name-box').fill('no_username');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#name-box').clear();
    await page.locator('.create-container').locator('#email-box').fill('no_username_email@email.com');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#name-box')).toBeFocused();

    await expect(page.getByText('div:id("no_username_email@email.com-user-cell")')).not.toBeVisible();
  });

  test('should not create user with invalid email or name', async({ page }) => {
    await page.locator('#create-user-form-button').click();

    await page.locator('.create-container').locator('#name-box').fill('valid_test_name');
    await page.locator('.create-container').locator('#email-box').fill('invalid_email@email.c');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#email-box').clear();
    await page.locator('.create-container').locator('#email-box').fill('invalid_email@');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#email-box').clear();
    await page.locator('.create-container').locator('#email-box').fill('invalid_email');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#name-box').clear();
    await page.locator('.create-container').locator('#email-box').fill('invalid_email@email.com');
    await page.locator('.create-container').locator('#name-box').fill('va');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#name-box')).toBeFocused();
  });

  test('should search and find user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await searchInTable(page, username);
    await expect(page.locator(`[id="${email}-user-cell"]`)).toBeVisible();

    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-user-cell"]`)).toBeVisible();
  });

  test('should search and not find user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await searchInTable(page, username);
    await expect(page.locator(`[id="${email}-user-cell"]`)).not.toBeVisible();

    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-user-cell"]`)).not.toBeVisible();
  });

  test('should edit username', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-user-cell"]`).getByTitle('Edit').click();
    await page.locator(`[id="${email}-new-name-input"]`).focus();
    await page.keyboard.type('123');
    await page.keyboard.press('Enter');

    await expect(page.locator(`[id="${email}-user-cell"]`)).toContainText(username+'123');
  });

  test('should try to delete username', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-user-cell"]`).getByTitle('Edit').click();
    await page.locator(`[id="${email}-new-name-input"]`).clear();
    await page.keyboard.press('Enter');
    await expect(page.locator(`[id="${email}-new-name-input"]`)).toBeFocused();
    await page.locator('#cancel-button').click();

    await expect(page.locator(`[id="${email}-user-cell"]`)).toContainText(username);
  });

  test('should cancel the process of creating user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await page.locator('#create-user-form-button').click();

    await page.locator('.create-container').locator('#name-box').fill(username);
    await page.locator('.create-container').locator('#email-box').fill(email);
    await page.locator('#cancel-user-creation-button').click();

    await expect(page.locator(`[id="${email}-user-cell"]`)).not.toBeVisible();
  });

  test('should check admin', async({ page }) => {
    await searchInTable(page, 'admin@iossifovlab.com');
    await expect(page.locator('#admin-list-item gpf-confirm-button')).not.toBeVisible();
    await expect(page.locator('[id="admin@iossifovlab.com-datasets-cell"]'))
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
    await expect(page.locator('[id="admin@iossifovlab.com-reset-password-button"]')).toBeVisible();
    await expect(page.locator('[id="admin@iossifovlab.com-reset-delete-user-button"]')).not.toBeVisible();
  });

  test('should add and remove group', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, 'denovo_helloworld');
    await page.waitForSelector('button:text("denovo_helloworld")');
    await page.getByRole('button', { name: 'denovo_helloworld' }).click();

    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText(email);
    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText('any_user');
    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText('denovo_helloworld');
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).toContainText('denovo_helloworld');

    await page.locator(`[id="${email}-groups-cell"] #denovo_helloworld-list-item gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();

    await expect(page.locator(`[id="${email}-groups-cell"]`)).not.toContainText('denovo_helloworld');
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).not.toContainText('denovo_helloworld');
  });
});

test.describe('Groups management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
  });

  test('should create and delete group with user and dataset', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    // add user
    await addUserToGroup(page, groupName, email);
    await expect(page.locator(`[id="${groupName}-users-cell"]`)).toContainText(email);
    await expect(page.getByText('Empty groups with no users or datasets will be deleted!')).not.toBeVisible();

    // add dataset
    await addDatasetToGroup(page, groupName, 'iossifov_2014_liftover');

    // check if the group is added
    await page.reload();
    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).toBeVisible();

    await deleteGroup(page, groupName);
    await deleteUser(page, email);
  });

  test('should create and delete group with user only', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    // add user
    await addUserToGroup(page, groupName, email);
    await expect(page.locator(`[id="${groupName}-users-cell"]`)).toContainText(email);
    await expect(page.getByText('Empty groups with no users or datasets will be deleted!')).not.toBeVisible();

    // check if the group is added
    await page.reload();
    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).toBeVisible();

    await deleteGroup(page, groupName);
    await deleteUser(page, email);
  });

  test('should create and delete group with dataset only', async({ page }) => {
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    await addDatasetToGroup(page, groupName, 'iossifov_2014_liftover');
    await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).toContainText('iossifov_2014_liftover');

    // check if the group is added
    await page.reload();
    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).toBeVisible();

    await deleteGroup(page, groupName);
  });

  test('should not create with no users or datasets', async({ page }) => {
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    await page.reload();
    await page.locator('a:text("Groups")').click();
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).not.toBeVisible();
  });

  test('should not create group with invalid name', async({ page }) => {
    await page.locator('a:text("Groups")').click();
    await page.locator('#create-group-form-button').click();

    await page.locator('#group-name-box').fill('c');
    await page.locator('#create-group-button').click();
    await expect(page.locator('#group-name-box')).toBeFocused();

    await page.locator('#group-name-box').clear();
    await page.locator('#group-name-box').fill('cc');
    await page.locator('#create-group-button').click();
    await expect(page.locator('#group-name-box')).toBeFocused();

    await page.locator('#cancel-group-creation-button').click();
  });

  test('should cancel the process of creating group', async({ page }) => {
    await page.locator('a:text("Groups")').click();

    await page.locator('#create-group-form-button').click();
    await page.locator('#group-name-box').fill('cancel_creation_group');
    await page.locator('#cancel-group-creation-button').click();
    await expect(page.locator('[id="cancel_creation_group-group-cell"]')).not.toBeVisible();
  });

  test('should fail to create group with already used name', async({ page }) => {
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    // add dataset to make the group valid
    await addDatasetToGroup(page, groupName, 'iossifov_2014_liftover');
    await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).toContainText('iossifov_2014_liftover');

    await page.locator('#create-group-form-button').click();
    await page.locator('#group-name-box').fill(groupName);
    await page.locator('#create-group-button').click();
    await expect(page.getByText(` '${groupName}' already exists choose another name! `)).toBeVisible();
  });

  test('should add and remove user and dataset from Group', async({ page }) => {
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
    await page.locator(`[id="${groupName}-users-cell"] [id="${email}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(`[id="${groupName}-users-cell"]`)).not.toContainText(email);

    // remove dataset
    await page.locator(`[id="${groupName}-datasets-cell"] [id="${datasetName}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).not.toContainText(datasetName);

    await expect(page.getByText('Empty groups with no users or datasets will be deleted!')).toBeVisible();
    await page.reload();
    await page.locator('a:text("Groups")').click();
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).not.toBeVisible();

    await deleteUser(page, email);
  });

  test('should add and remove users and groups from Users and Groups', async({ page }) => {
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
    await page.locator('a:text("Users")').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText(groupName1);

    // add the second group to the user in Users
    await page.locator(`[id="${email}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName2);
    await page.waitForSelector(`button:text("${groupName2}")`);
    await page.getByRole('button', { name: groupName2 }).click();
    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText(groupName2);

    // go and check users list of the second group in Groups
    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName2);
    await expect(page.locator(`[id="${groupName2}-users-cell"]`)).toContainText(email);

    // delete both groups
    await deleteGroup(page, groupName1);
    await deleteGroup(page, groupName2);

    // check groups list of the user
    await page.locator('a:text("Users")').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-groups-cell"]`)).not.toContainText(groupName1);
    await expect(page.locator(`[id="${email}-groups-cell"]`)).not.toContainText(groupName2);

    await deleteUser(page, email);
  });

  test('should check if new groups and any_user group when creating user', async({ page }) => {
    const username1 = utils.getRandomString();
    const email1 = `${username1}@mail.com`;
    await utils.createUser(page, email1, username1);

    const username2 = utils.getRandomString();
    const email2 = `${username2}@mail.com`;
    await utils.createUser(page, email2, username2);

    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, email1);
    await expect(page.locator(`[id="${email1}-group-cell"]`)).toBeVisible();
    await searchInTable(page, email2);
    await expect(page.locator(`[id="${email2}-group-cell"]`)).toBeVisible();

    await searchInTable(page, 'any_user');
    await expect(page.locator('[id="any_user-users-cell"]')).toContainText(email1);
    await expect(page.locator('[id="any_user-users-cell"]')).toContainText(email2);

    await deleteUser(page, email1);
    await deleteUser(page, email2);

    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, email1);
    await expect(page.locator(`[id="${email1}-group-cell"]`)).not.toBeVisible();
    await searchInTable(page, email2);
    await expect(page.locator(`[id="${email2}-group-cell"]`)).not.toBeVisible();

    await searchInTable(page, 'any_user');
    await expect(page.locator('[id="any_user-users-cell"]')).not.toContainText(email1);
    await expect(page.locator('[id="any_user-users-cell"]')).not.toContainText(email2);
  });

  test('should check if the new group is deleted after removing it in Users', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    await page.locator('a:text("Users")').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await page.locator(`[id="${email}-groups-cell"] [id="${groupName}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(`[id="${email}-groups-cell"] [id="${groupName}-list-item"]`)).not.toBeVisible();

    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).not.toBeVisible();

    await deleteUser(page, email);
  });

  test('should check if the new group is deleted after deleting the user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    await deleteUser(page, email);

    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(page.locator(`[id="${groupName}-group-cell"]`)).not.toBeVisible();
  });
});

test.describe('Datasets management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await loginLiteralAdmin(page);
    await navigateToManagement(page);
  });

  test('should add group to user and check data in Datasets', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = 'vcf_helloworld';

    // add group to user
    await page.locator(`[id="${email}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName);
    await page.waitForSelector(`button:text("${groupName}")`);
    await page.getByRole('button', { name: groupName }).click();

    // check datasets of the user
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).toContainText(groupName);

    // check dataset in Datasets
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${groupName}-users-list-cell"]`)).toContainText(username);
    await expect(page.locator(`[id="${groupName}-users-list-cell"]`)).toContainText(email);

    await deleteUser(page, email);

    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${groupName}-users-list-cell"]`)).not.toContainText(username);
    await expect(page.locator(`[id="${groupName}-users-list-cell"]`)).not.toContainText(email);
  });

  test('should create group, add datasets and check data in Datasets', async({ page }) => {
    const groupName = utils.getRandomString();
    await createGroup(page, groupName);

    const datasetName1 = 'iossifov_2014_liftover';
    const datasetName2 = 'vcf_helloworld';
    await addDatasetToGroup(page, groupName, datasetName1);
    await addDatasetToGroup(page, groupName, datasetName2);

    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${datasetName1}-groups-cell"]`)).toContainText('any_dataset');
    await expect(page.locator(`[id="${datasetName1}-groups-cell"]`)).toContainText(datasetName1);
    await expect(page.locator(`[id="${datasetName1}-groups-cell"]`)).toContainText(groupName);
    await expect(page.locator(`[id="${datasetName2}-groups-cell"]`)).toContainText('any_dataset');
    await expect(page.locator(`[id="${datasetName2}-groups-cell"]`)).toContainText(datasetName2);
    await expect(page.locator(`[id="${datasetName2}-groups-cell"]`)).toContainText(groupName);

    await deleteGroup(page, groupName);

    await expect(async() => {
      await page.getByRole('tab', { name: 'Datasets' }).click();
      await expect(page.locator(`[id="${datasetName1}-groups-cell"]`)).not.toContainText(groupName);
      await expect(page.locator(`[id="${datasetName2}-groups-cell"]`)).not.toContainText(groupName);
    }).toPass({intervals: [1000]});
  });

  test('should create group, add dataset and users and check data in Datasets', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'iossifov_2014_liftover';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);
    await addDatasetToGroup(page, groupName, datasetName);

    // check datasets of the user
    await page.locator('a:text("Users")').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).toContainText(datasetName);

    // check dataset in Datasets
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).toContainText(username);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).toContainText(email);
    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).toContainText(groupName);

    // remove dataset from the group
    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await page.locator(`[id="${groupName}-datasets-cell"] [id="${datasetName}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(`[id="${groupName}-datasets-cell"] [id="${datasetName}-list-item"]`)).not.toBeVisible();

    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).not.toContainText(groupName);

    await deleteUser(page, email);

    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(username);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(email);
  });

  test('should add and remove groups in Datasets', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'vcf_helloworld';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    // add the group to dataset in Datasets
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await page.locator(`[id="${datasetName}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName);
    await page.waitForSelector(`button:text("${groupName}")`);
    await page.getByRole('button', { name: groupName }).click();

    // check users list of dataset
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).toContainText(username);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).toContainText(email);

    // check group list of dataset
    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).toContainText(groupName);

    // remove the group from the dataset
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await page.locator(`[id="${datasetName}-groups-cell"] [id="${groupName}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    // tb-pa6: drop the meaningless `${groupName}-datasets-cell` assertion
    // (only renders on the Groups tab; not.toBeVisible() against a
    // non-existent locator passes trivially). Lines below verify the
    // removal correctly via the `${datasetName}-groups-cell`
    // (Datasets-tab) locator.
    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).not.toContainText(groupName);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(email);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(username);
  });

  test('should add groups with user to dataset and delete the user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'denovo_helloworld';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    // add the group to dataset in Datasets
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await page.locator(`[id="${datasetName}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, groupName);
    await page.waitForSelector(`button:text("${groupName}")`);
    await page.getByRole('button', { name: groupName }).click();

    // check users list of dataset
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).toContainText(username);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).toContainText(email);

    // check group list of dataset
    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).toContainText(groupName);

    // check dataset cell of the user in Users
    await page.locator('a:text("Users")').click();
    await page.waitForSelector('gpf-users-table');
    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).toContainText(datasetName);

    await deleteUser(page, email);

    // check the group in Groups
    await page.locator('a:text("Groups")').click();
    await page.waitForSelector('gpf-groups-table');
    await searchInTable(page, groupName);
    await expect(page.locator(`[id="${groupName}-users-cell"]`)).not.toContainText(email);
    await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).not.toContainText(email);

    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).toContainText(groupName);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(email);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(username);
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
    const managementUrl = `${utils.frontendUrl}/management`;

    await loginLiteralAdmin(page);

    await page.locator('a:text("Management")').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(managementUrl);
  });

  test(`should check navigation bar for the right elements for ${LITERAL_ADMIN_EMAIL} user`, async({ page }) => {
    await loginLiteralAdmin(page);

    const navigationTabs = ['Home', 'Datasets', 'Gene profiles', 'User profile', 'Management', 'About'];
    await expect(page.locator('#header a')).toHaveCount(navigationTabs.length);

    for (const tab of navigationTabs) {
      await expect(page.locator('#header a').getByText(tab)).toBeVisible();
    }
  });

  test('should login admin and give user access rights for Hello World Genotypes, ' +
       'then login user and verify his rights', async({ page }) => {
    const newUserPasswordSuffix = '!!__3456';
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-groups-cell"]`).getByRole(
      'button', { name: 'Add' }
    ).click();
    await page.getByRole('textbox', { name: 'Search' }).focus();
    await page.keyboard.type('helloworld_genotypes');
    await page.locator('button.add-item-button').filter({ hasText: 'helloworld_genotypes' }).click();
    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();
    await utils.logout(page);

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill('secret' + newUserPasswordSuffix);
    await page.locator('#id_new_password2').fill('secret' + newUserPasswordSuffix);
    await page.locator('input[value="Reset password"]').click();
    await expect(page).toHaveURL(`${utils.frontendUrl}/home`);

    await utils.login(page, email, 'secret' + newUserPasswordSuffix);

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    await expect(page.locator('#register-alert')).toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    await expect(page.locator('#register-alert')).toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    await expect(page.locator('#register-alert')).toBeVisible();
  });

  test('should login admin and give user access rights for ALL Genotypes, ' +
     'then login user and verify his rights', async({ page }) => {
    const newUserPasswordSuffix = '!!__3456';
    await loginLiteralAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-groups-cell"]`).getByRole(
      'button', { name: 'Add' }
    ).click();
    await page.getByRole('textbox', { name: 'Search' }).fill('ALL_genotypes');
    await page.getByRole('button', { name: 'ALL_genotypes', exact: true }).click();
    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();
    await utils.logout(page);

    await page.goto(await utils.getLinkInEmail(page, email), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill('secret' + newUserPasswordSuffix);
    await page.locator('#id_new_password2').fill('secret' + newUserPasswordSuffix);
    await page.locator('input[value="Reset password"]').click();

    await expect(page).toHaveURL(`${utils.frontendUrl}/home`);

    await utils.login(page, email, 'secret' + newUserPasswordSuffix);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    await expect(page.locator('#register-alert')).not.toBeVisible();

    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    await expect(page.locator('#register-alert')).toBeVisible();
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
    // check if Genotype browser is disabled when no user is logged in
    await utils.logout(page);
    const study = utils.datasetIds.vcfHelloWorld;
    const group = 'any_user';
    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item disabled-tool');

    // add any_user group to study
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);

    await page.locator(`[id="${study}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, group);
    await page.waitForSelector(`button:text("${group}")`);
    await page.getByRole('button', { name: group }).click();

    await expect(page.locator(`[id="${study}-groups-cell"]`)).toContainText(group);

    // check if Genotype browser is enabled when no user is logged in
    await utils.logout(page);

    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    // remove any_user from list of groups of the study
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);
    await page.locator(`[id="${study}-groups-cell"] [id="${group}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    // tb-pa6: assert against the locator visible on the Datasets tab
    // (where this test sits). The previous assertion targeted
    // `${group}-datasets-cell` which only renders on the Groups tab —
    // .not.toBeVisible() against a never-rendered locator passes
    // trivially, leaving an actually-failed Remove click silent.
    await expect(page.locator(`[id="${study}-groups-cell"] [id="${group}-list-item"]`)).not.toBeVisible();
  });

  test('should give rights for vcf_helloworld to researcher', async({ page }) => {
    // check if Genotype browser is disabled when no user is logged in
    await utils.logout(page);

    const study = utils.datasetIds.vcfHelloWorld;
    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item disabled-tool');

    // add group to reasearcher
    const researcher = 'research@iossifovlab.com';
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, study);
    await page.waitForSelector(`button:text("${study}")`);
    await page.getByRole('button', { name: study }).click();

    await utils.logout(page);
    // check if Genotype browser is enabled when researcher is logged in
    await utils.login(page, researcher, 'secret');

    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    // remove group from groups list of research
    await utils.logout(page);
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"] [id="${study}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();

    await expect(page.locator(`[id="${researcher}-groups-cell"]`)).not.toContainText(study);
  });

  test('should give rights for pheno_helloworld to any_user', async({ page }) => {
    const study = utils.datasetIds.phenoHelloWorld;
    const group = 'any_user';

    // check if Phenotype browser download is disabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).toContainClass('disabled-download');

    // add any_user group to pheno study
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);

    await page.locator(`[id="${study}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, group);
    await page.waitForSelector(`button:text("${group}")`);
    await page.getByRole('button', { name: group }).click();

    await expect(page.locator(`[id="${study}-groups-cell"]`)).toContainText(group);

    // check if Phenotype browser is enabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).not.toContainClass('disabled-download');

    // remove any_user from list of groups of the pheno study
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);
    await page.locator(`[id="${study}-groups-cell"] [id="${group}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    // tb-pa6: assert against the Datasets-tab locator (see twin fix
    // ~85 lines above for vcf_helloworld → any_user).
    await expect(page.locator(`[id="${study}-groups-cell"] [id="${group}-list-item"]`)).not.toBeVisible();
  });

  test('should give rights for pheno_helloworld to researcher', async({ page }) => {
    const study = utils.datasetIds.phenoHelloWorld;
    const researcher = 'research@iossifovlab.com';

    // check if Phenotype browser download is disabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).toContainClass('disabled-download');

    // add pheno group to reasearcher
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"]`).getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, study);
    await page.waitForSelector(`button:text("${study}")`);
    await page.getByRole('button', { name: study }).click();

    await utils.logout(page);
    // check if Phenotype browser download is enabled when researcher is logged in
    await utils.login(page, researcher, 'secret');

    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).not.toContainClass('disabled-download');

    // remove pheno group from groups list of research
    await utils.logout(page);
    await loginLiteralAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"] [id="${study}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();

    await expect(page.locator(`[id="${researcher}-groups-cell"]`)).not.toContainText(study);
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
    await expect(page.locator('gpf-dataset-description')).toBeVisible();
  });

  test('should display empty description placeholder text', async({ page }) => {
    await expect(page.locator('#empty-description')).toBeVisible();
    await expect(
      page.locator('#empty-description')
    ).toHaveText('Empty description. Write a description using the pencil button to the right.');
  });

  test('should display edit icon', async({ page }) => {
    await expect(page.locator('#edit-icon')).toBeVisible();
  });

  test('should display angular markdown editor after clicking the edit button', async({ page }) => {
    await expect(page.locator('.editor')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.locator('.editor')).toBeVisible();
  });

  test('should display preview button', async({ page }) => {
    await expect(page.getByText('Preview')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.getByText('Preview')).toBeVisible();
  });

  test('should display save button', async({ page }) => {
    await expect(page.getByText('Save')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.getByText('Save')).toBeVisible();
  });

  test('should display close button', async({ page }) => {
    await expect(page.getByText('Close')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.getByText('Close')).toBeVisible();
  });

  test('should display the editor header bar', async({ page }) => {
    await expect(page.locator('.md-header')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.locator('.md-header')).toBeVisible();
  });

  test('should hide the edit button after clicking it', async({ page }) => {
    await expect(page.locator('#edit-icon')).toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.locator('#edit-icon')).not.toBeVisible();
    await page.getByText('Close').click();
    await expect(page.locator('#edit-icon')).toBeVisible();
  });

  test('should save the markdown', async({ page }) => {
    await expect(page.locator('#empty-description')).toBeVisible();
    await expect(page.locator('markdown p')).not.toBeVisible();

    // The SPA's markdown-editor save() does an optimistic UI update + a
    // fire-and-forget POST to /datasets/description/<id>. Without waiting
    // for the response the page can be torn down before the POST reaches
    // the backend, leaving stale content for the next test run.
    const isDescriptionSave = (resp: import('@playwright/test').Response): boolean =>
      resp.url().includes('/api/v3/datasets/description/') && resp.request().method() === 'POST';

    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').type('TEST DESCRIPTION ASDF');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      page.getByText('Save').click(),
    ]);
    await expect(page.locator('markdown p')).toHaveText('TEST DESCRIPTION ASDF');
    await expect(page.locator('#empty-description')).not.toBeVisible();

    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').fill('');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      page.getByText('Save').click(),
    ]);
    await expect(page.locator('#empty-description')).toBeVisible();
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
    await page.locator('a:text("Management")').click();

    await page.locator('[id="user_iossifov_2014@iossifovlab.com-groups-cell"]')
      .getByRole('button', { name: 'Add' }).click();
    await page.waitForSelector('.add-item-button');
    await page.getByRole('textbox', { name: 'Search' }).focus();
    await page.keyboard.type('iossifov_2014_liftover');
    await page.waitForSelector('button:text("iossifov_2014_liftover")');
    await page.getByRole('button', { name: 'iossifov_2014_liftover' }).click();
    await page.mouse.click(0, 0); // close the menu

    await page.locator('#header a:text("Datasets")').click();
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

    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').fill('IOSSIFOV TEST DESCRIPTION');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      page.getByText('Save').click(),
    ]);
    await utils.logout(page);

    await utils.login(page, 'user_iossifov_2014@iossifovlab.com');
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    await expect(page.locator('markdown p')).toHaveText('IOSSIFOV TEST DESCRIPTION');
    await expect(page.locator('#edit-icon')).not.toBeVisible();
    await utils.logout(page);

    await loginLiteralAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    // tb-pa6: assert the description is loaded before opening the
    // editor. Clicking #edit-icon before the GET completes leaves
    // markdown-editor's initialMarkdown empty, which makes the
    // subsequent fill('') + Save a no-op (markdown===initialMarkdown,
    // writeEvent never emitted, POST never fires, waitForResponse
    // times out).
    await expect(page.locator('markdown p')).toHaveText('IOSSIFOV TEST DESCRIPTION');
    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').fill('');
    await Promise.all([
      page.waitForResponse(isDescriptionSave),
      page.getByText('Save').click(),
    ]);

    await page.locator('a:text("Management")').click();
    await page.locator(
      '[id="user_iossifov_2014@iossifovlab.com-groups-cell"] #iossifov_2014_liftover-list-item gpf-confirm-button'
    ).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(
      '[id="user_iossifov_2014@iossifovlab.com-groups-cell"]')
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
    await page.locator('#edit-icon').click();
    await expect(page.locator('.editor')).toBeVisible();
    await page.locator('gpf-markdown-editor').locator('textarea').fill('Test description');
    await page.getByText('Save').click();

    await expect(page.locator('.editor')).not.toBeVisible();
    await page.reload();
    await expect(page.locator('#edit-container p')).toHaveText('Test description');

    await page.locator('#edit-icon').click();
    await page.locator('gpf-markdown-editor').locator('textarea').clear();

    await page.getByText('Save').click();
    await expect(page.locator('#empty-description')).toBeVisible();
  });

  test('should check if editing description is disabled when no access rights', async({ page }) => {
    await page.locator('#edit-icon').click();
    await page.locator('gpf-markdown-editor').locator('textarea').fill('Test description');
    await page.getByText('Save').click();


    await utils.logout(page);
    await page.waitForSelector('gpf-home');
    await expect(page.locator('#edit-container p')).toHaveText('Test description');
    await expect(page.locator('#edit-icon')).not.toBeVisible();

    await loginLiteralAdmin(page);
    await page.waitForSelector('gpf-home');

    await page.locator('#edit-icon').click();
    await page.locator('gpf-markdown-editor').locator('textarea').clear();

    await page.getByText('Save').click();
    await expect(page.locator('#empty-description')).toBeVisible();

    await utils.logout(page);
    await page.waitForSelector('gpf-home');
    await expect(page.locator('gpf-markdown-editor')).not.toBeVisible();
  });
});

async function createGroup(page: Page, name: string): Promise<void> {
  await page.locator('a:text("Groups")').click();
  await page.locator('#create-group-form-button').click();
  await page.locator('#group-name-box').fill(name);
  await page.locator('#create-group-button').click();
  await expect(page.getByText(`${name}Empty groups with no users or datasets will be deleted!`)).toBeVisible();
}

async function deleteGroup(page: Page, name: string): Promise<void> {
  await page.locator('a:text("Groups")').click();
  await page.waitForSelector('gpf-groups-table');
  await searchInTable(page, name);
  await page.locator(`[id="${name}-delete-group-button"]`).click();

  const permissionResponse = page.waitForResponse(resp =>
    (resp.url().includes('revoke-permission') && resp.status() === 200)
    || (resp.url().includes('remove-user') && resp.status() === 204)
  );
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  await permissionResponse;

  await expect(page.locator(`[id="${name}-group-cell"]`)).not.toBeVisible();
}

async function addUserToGroup(page: Page, groupName: string, email: string): Promise<void> {
  await page.locator(`[id="${groupName}-users-cell"]`).getByRole('button', { name: 'Add' }).click();
  await page.waitForSelector('.add-item-button');
  await searchInMenu(page, email);
  await page.waitForSelector(`button:text("${email}")`);
  await page.getByRole('button', { name: email }).click();
  await page.mouse.click(0, 0); // close the menu
  await expect(page.locator(`[id="${groupName}-users-cell"]`)).toContainText(email);
}

async function addDatasetToGroup(page: Page, groupName: string, datasetName: string): Promise<void> {
  await page.locator(`[id="${groupName}-datasets-cell"]`).getByRole('button', { name: 'Add' }).click();
  await page.waitForSelector('.add-item-button');
  await searchInMenu(page, datasetName);
  await page.waitForSelector(`button:text("${datasetName}")`);
  await page.getByRole('button', { name: datasetName }).click();
  await page.mouse.click(0, 0); // close the menu
  await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).toContainText(datasetName);
}

async function deleteUser(page: Page, email: string): Promise<void> {
  await page.locator('a:text("Users")').click();
  await page.waitForSelector('gpf-users-table');
  await searchInTable(page, email);
  await page.locator(`[id="${email}-delete-user-button"]`).click();

  const deleteResponse = page.waitForResponse(
    resp => resp.request().method() === 'DELETE' && resp.status() === 204
  );
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  await deleteResponse;
}

async function searchInTable(page: Page, name: string): Promise<void> {
  await page.locator('#search-field').clear();
  await page.locator('#search-field').focus();
  await page.keyboard.type(name);
}

async function searchInMenu(page: Page, name: string): Promise<void> {
  await page.getByRole('textbox', { name: 'Search' }).clear();
  await page.getByRole('textbox', { name: 'Search' }).focus();
  await page.keyboard.type(name);
}

async function navigateToManagement(page: Page): Promise<void> {
  await page.locator('a:text("Management")').click();
  await page.waitForSelector('.grid-cell');
}