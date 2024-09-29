import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('Management tests for reset password in Users', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
  });

  test('should reset password', async({ page }) => {
    await utils.login(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText(email).click();
    await page.goto(await page.locator('#preview-plain > a').getAttribute('href'), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill(password);
    await page.locator('#id_new_password2').fill(password);
    await page.locator('.login-button').click();

    await page.waitForSelector('gpf-gene-browser');
    await expect(page.locator('#log-out-button')).toBeVisible();
    await page.locator('#log-out-button').click();
  });

  test('should reset password when login', async({ page }) => {
    await utils.loginAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await Promise.all([
      await page.locator('#log-out-button').click(),
      await page.waitForResponse(resp => resp.url().includes('logout') && resp.status() === 204)
    ]);

    await page.locator('#log-in-button').click();
    await page.locator('#forgotten-password').click();
    await page.locator('#id_email').fill(email);
    await page.getByText('Reset password').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText(email).click();
    await page.goto(await page.locator('#preview-plain > a').getAttribute('href'), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill(password);
    await page.locator('#id_new_password2').fill(password);
    await page.getByText('Reset password').click();
    await utils.login(page, email, password);

    await page.waitForSelector('#permission-denied-prompt');
    await expect(page.locator('#log-out-button')).toBeVisible();
    await page.locator('#log-out-button').click();
  });
});

test.describe('Users management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
  });
  test('should not create user with already used email', async({ page }) => {
    await page.locator('a:text("Management")').click();
    await utils.createUser(page, 'used_email@email.com', 'used_name');

    await page.locator('#create-user-form-button').click();
    await page.locator('#name-box').fill('used_name');
    await page.locator('#email-box').fill('used_email@email.com');
    await page.locator('#create-user-button').click();

    await expect(page.getByText(' Error: wdae user with this email already exists. ')).toBeVisible();
    await deleteUser(page, 'used_email@email.com');
  });

  test('should not create user with no email or name', async({ page }) => {
    await page.locator('a:text("Management")').click();

    await page.locator('#create-user-form-button').click();
    await page.locator('#name-box').fill('no_username');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#name-box').clear();
    await page.locator('#email-box').fill('no_username_email@email.com');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#name-box')).toBeFocused();

    await expect(page.getByText('div:id("no_username_email@email.com-user-cell")')).not.toBeVisible();
  });

  test('should not create user with invalid email or name', async({ page }) => {
    await page.locator('a:text("Management")').click();

    await page.locator('#create-user-form-button').click();

    await page.locator('#name-box').fill('valid_test_name');
    await page.locator('#email-box').fill('invalid_email@email.c');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#email-box').clear();
    await page.locator('#email-box').fill('invalid_email@');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#email-box').clear();
    await page.locator('#email-box').fill('invalid_email');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#email-box')).toBeFocused();

    await page.locator('#name-box').clear();
    await page.locator('#email-box').fill('invalid_email@email.com');
    await page.locator('#name-box').fill('va');
    await page.locator('#create-user-button').click();
    await expect(page.locator('#name-box')).toBeFocused();
  });

  test('should search and find user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await searchInTable(page, username);
    await expect(page.locator(`[id="${email}-user-cell"]`)).toBeVisible();

    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-user-cell"]`)).toBeVisible();
  });

  test('should search and not find user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await searchInTable(page, username);
    await expect(page.locator(`[id="${email}-user-cell"]`)).not.toBeVisible();

    await searchInTable(page, email);
    await expect(page.locator(`[id="${email}-user-cell"]`)).not.toBeVisible();
  });

  test('should edit username', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await page.locator('a:text("Management")').click();
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
    await page.locator('a:text("Management")').click();
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

    await page.locator('a:text("Management")').click();
    await page.locator('#create-user-form-button').click();

    await page.locator('#name-box').fill(username);
    await page.locator('#email-box').fill(email);
    await page.locator('#cancel-user-creation-button').click();

    await expect(page.locator(`[id="${email}-user-cell"]`)).not.toBeVisible();
  });

  test('should check admin', async({ page }) => {
    await page.locator('a:text("Management")').click();
    await searchInTable(page, 'admin@iossifovlab.com');
    await expect(page.locator('#admin-list-item gpf-confirm-button')).not.toBeVisible();
    await expect(page.locator('[id="admin@iossifovlab.com-datasets-cell"]'))
      .toHaveText('ALL GenotypesCOMP Genotypescomp_allcomp_denovocomp_vcfiossifov_2014multi');
    await expect(page.locator('[id="admin@iossifovlab.com-reset-password-button"]')).toBeVisible();
    await expect(page.locator('[id="admin@iossifovlab.com-reset-delete-user-button"]')).not.toBeVisible();
  });

  test('should add and remove group', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await page.locator('a:text("Management")').click();
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-groups-cell"]`).getByText('Add').click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, 'comp_all');
    await page.waitForSelector('button:text("comp_all")');
    await page.getByRole('button', { name: 'comp_all' }).click();

    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText(email);
    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText('any_user');
    await expect(page.locator(`[id="${email}-groups-cell"]`)).toContainText('comp_all');
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).toContainText('comp_all');

    await page.locator(`[id="${email}-groups-cell"] #comp_all-list-item gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();

    await expect(page.locator(`[id="${email}-groups-cell"]`)).not.toContainText('comp_all');
    await expect(page.locator(`[id="${email}-datasets-cell"]`)).not.toContainText('comp_all');
  });
});

test.describe('Groups management', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
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
    await addDatasetToGroup(page, groupName, 'iossifov_2014');

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

    await addDatasetToGroup(page, groupName, 'iossifov_2014');
    await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).toContainText('iossifov_2014');

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
    await addDatasetToGroup(page, groupName, 'iossifov_2014');
    await expect(page.locator(`[id="${groupName}-datasets-cell"]`)).toContainText('iossifov_2014');

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

    const datasetName = 'iossifov_2014';

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

    const datasetName = 'iossifov_2014';

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
    await page.locator(`[id="${email}-groups-cell"]`).getByText('Add').click();
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
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
  });

  test('should add group to user and check data in Datasets', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const groupName = 'comp_all';

    // add group to user
    await page.locator(`[id="${email}-groups-cell"]`).getByText('Add').click();
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

    const datasetName1 = 'iossifov_2014';
    const datasetName2 = 'comp_all';
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

    await page.getByRole('tab', { name: 'Datasets' }).click();
    await expect(page.locator(`[id="${datasetName1}-groups-cell"]`)).not.toContainText(groupName);
    await expect(page.locator(`[id="${datasetName2}-groups-cell"]`)).not.toContainText(groupName);
  });

  test('should create group, add dataset and users and check data in Datasets', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'iossifov_2014';

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

    const datasetName = 'comp_denovo';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    // add the group to dataset in Datasets
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await page.locator(`[id="${datasetName}-groups-cell"]`).getByText('Add').click();
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
    await expect(page.locator(`[id="${groupName}-datasets-cell"] [id="${datasetName}-list-item"]`)).not.toBeVisible();

    await expect(page.locator(`[id="${datasetName}-groups-cell"]`)).not.toContainText(groupName);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(email);
    await expect(page.locator(`[id="${datasetName}-users-cell"]`)).not.toContainText(username);
  });

  test('should add groups with user to dataset and delete the user', async({ page }) => {
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    await utils.createUser(page, email, username);

    const datasetName = 'comp_denovo';

    const groupName = utils.getRandomString();
    await createGroup(page, groupName);
    await addUserToGroup(page, groupName, email);

    // add the group to dataset in Datasets
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await page.locator(`[id="${datasetName}-groups-cell"]`).getByText('Add').click();
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

  await Promise.all([
    await page.getByRole('button', { name: 'Delete', exact: true }).click(),
    await page.waitForResponse(resp =>
      (resp.url().includes('revoke-permission') && resp.status() === 200)
      || (resp.url().includes('remove-user') && resp.status() === 204)
    )
  ]);

  await expect(page.locator(`[id="${name}-group-cell"]`)).not.toBeVisible();
}

async function addUserToGroup(page: Page, groupName: string, email: string): Promise<void> {
  await page.locator(`[id="${groupName}-users-cell"]`).getByText('Add').click();
  await page.waitForSelector('.add-item-button');
  await searchInMenu(page, email);
  await page.waitForSelector(`button:text("${email}")`);
  await page.getByRole('button', { name: email }).click();
  await page.mouse.click(0, 0); // close the menu
  await expect(page.locator(`[id="${groupName}-users-cell"]`)).toContainText(email);
}

async function addDatasetToGroup(page: Page, groupName: string, datasetName: string): Promise<void> {
  await page.locator(`[id="${groupName}-datasets-cell"]`).getByText('Add').click();
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

  await Promise.all([
    await page.getByRole('button', { name: 'Delete', exact: true }).click(),
    await page.waitForResponse(
      resp => resp.request().method() === 'DELETE' && resp.status() === 204
    )
  ]);
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