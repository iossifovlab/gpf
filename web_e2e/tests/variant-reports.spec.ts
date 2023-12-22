import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';

const tags: string[] = [
  'tag_nuclear_family',
  'tag_quad_family',
  'tag_trio_family',
  'tag_simplex_family',
  'tag_multiplex_family',
  'tag_control_family',
  'tag_affected_dad_family',
  'tag_affected_mom_family',
  'tag_affected_prb_family',
  'tag_affected_sib_family',
  'tag_unaffected_dad_family',
  'tag_unaffected_mom_family',
  'tag_unaffected_prb_family',
  'tag_unaffected_sib_family',
  'tag_male_prb_family',
  'tag_female_prb_family',
  'tag_missing_mom_family',
  'tag_missing_dad_family'
];

test.describe('Variant reports tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.getByText(utils.datasetIds.iossifov2014, {exact: true}).click();
    await page.getByText('Dataset Statistics').click();
  });

  test('should display the correct elements in the families by number tab', async({ page }) => {
    await page.getByText('Families by number').click();
    await expect(page.locator('#download-total-families')).toBeVisible();
    await expect(page.locator('#families-by-number-select')).toBeVisible();
    await expect(page.locator('#families-by-number-div')).toBeVisible();

    await page.getByText('De Novo variants').click();
    await expect(page.locator('#download-total-families')).not.toBeVisible();
    await expect(page.locator('#families-by-number-select')).not.toBeVisible();
    await expect(page.locator('#families-by-number-div')).not.toBeVisible();
  });

  test('should display the correct elements in the families by pedigree tab', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await expect(page.locator('#families-by-pedigree-select')).toBeVisible();
    await expect(page.locator('#download-button')).toBeVisible();
    await expect(page.locator('#families-by-pedigree-div')).toBeVisible();
    await expect(page.getByText('Select tags')).toBeVisible();

    await page.getByText('De Novo variants').click();
    await expect(page.locator('#families-by-pedigree-select')).not.toBeVisible();
    await expect(page.locator('#download-button')).not.toBeVisible();
    await expect(page.locator('#families-by-pedigree-div')).not.toBeVisible();
    await expect(page.getByText('Select tags')).not.toBeVisible();
  });

  test('should display the correct elements in the families by denovo tab', async({ page }) => {
    await page.getByText('De Novo variants').click();
    await expect(page.locator('#denovo-variants-select')).toBeVisible();
    await expect(page.locator('#de-novo-variants-legend-report')).toBeVisible();
    await expect(page.locator('#denovo-variants-div')).toBeVisible();

    await page.getByText('Families by number').click();
    await expect(page.locator('#denovo-variants-select')).not.toBeVisible();
    await expect(page.locator('#de-novo-variants-legend-report')).not.toBeVisible();
    await expect(page.locator('#denovo-variants-div')).not.toBeVisible();
  });

  [
    {option: 'Affected Status', legendElements: ['affected', 'unaffected']},
    {option: 'Role', legendElements: ['mom', 'dad', 'proband', 'sibling']},
    {option: 'Phenotype', legendElements: ['autism', 'unaffected']}
  ].forEach(data => {
    test('should check content of the legend for ' + data.option +
      ' option in the families by pedigree tab', async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await expect(page.locator('#expand-legend-button')).toBeVisible();
      await expect(page.locator('#legend')).not.toBeVisible();
      await page.locator('#families-by-pedigree-select').selectOption(data.option);

      await page.locator('#expand-legend-button').click();
      await expect(page.locator('#legend')).toBeVisible();

      await expect(page.locator('.legend-item')).toHaveCount(data.legendElements.length);

      await expect(page.locator('#legend')).toContainText(data.legendElements.join(''));

      await page.locator('#expand-legend-button').click();
      await expect(page.locator('#legend')).not.toBeVisible();
    });
  });

  test('should check content of the select in the families by pedigree tab', async({ page }) => {
    await page.getByText('Families by pedigree').click();

    await expect(page.locator('#families-by-pedigree-select option')).toHaveCount(3);

    const option1 = await page.locator('#families-by-pedigree-select option').nth(0).textContent();
    expect(['Affected Status', 'Role', 'Phenotype']).toContain(option1);

    const option2 = await page.locator('#families-by-pedigree-select option').nth(1).textContent();
    expect(['Affected Status', 'Role', 'Phenotype']).toContain(option2);

    const option3 = await page.locator('#families-by-pedigree-select option').nth(2).textContent();
    expect(['Affected Status', 'Role', 'Phenotype']).toContain(option3);
  });

  test('should open, close and check content for selecting tags', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await expect(page.getByText('Select tags')).toBeVisible();
    await expect(page.locator('#tags-modal-content')).not.toBeVisible();

    await page.getByText('Select tags').click();
    await expect(page.locator('#tags-modal-content')).toBeVisible();
    await expect(page.locator('#search-tags')).toBeVisible();
    await expect(page.locator('#uncheck-button')).toBeVisible();
    await expect(page.locator('#tag-list')).toBeVisible();

    await expect(page.locator('#tag-list')).toContainText(tags.join(''));

    await page.mouse.click(0, 0);
    await expect(page.locator('#tags-modal-content')).not.toBeVisible();
  });

  ['n', 'ro', 'lex'].forEach(searchValue => {
    test(`should search and find tags with ${searchValue}`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await page.getByText('Select tags').click();
      await page.locator('#search-tags').focus();
      await page.keyboard.type(searchValue);

      await Promise.all(tags.map(async(tag) => {
        if (tag.includes(searchValue)) {
          await expect(page.locator(`#${tag}-tag`)).toBeEnabled();
        } else {
          await expect(page.locator(`#${tag}-tag`)).toBeDisabled();
        }
      }));
      await page.locator('#search-tags').clear();
    });
  });

  ['cot', 'riof', 'tsf', 'as'].forEach(searchValue => {
    test(`should show nothing found when searching tags with ${searchValue}`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await page.getByText('Select tags').click();
      await page.locator('#search-tags').focus();
      await page.keyboard.type(searchValue);

      await Promise.all(tags.map(async(tag) => {
        await expect(page.locator(`#${tag}-tag`)).toBeDisabled();
      }));
      await page.locator('#search-tags').clear();
    });
  });

  [
    {tag: tags[0], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106', '6', '3']},
    {tag: tags[1], expectedPedigreeCounts: ['877', '789', '128', '107']},
    {tag: tags[2], expectedPedigreeCounts: ['500', '106', '6', '3']},
    {tag: tags[3], expectedPedigreeCounts: ['877', '789', '500', '128', '107', '106']},
    {tag: tags[5], expectedPedigreeCounts: ['6', '3']},
    {tag: tags[15], expectedPedigreeCounts: ['128', '107', '106']}
  ].forEach(data => {
    test(`should check pedigree by filtering with single tag ${data.tag}`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await page.getByText('Select tags').click();
      await page.locator(`#${data.tag}-tag`).setChecked(true, {force: true});
      await page.mouse.click(0, 0); // close modal

      await expect(page.locator('.pedigree-cell')).toHaveCount(data.expectedPedigreeCounts.length);
      await Promise.all(data.expectedPedigreeCounts.map(async(count, i) => {
        await expect(page.locator('.pedigree-cell').nth(i)).toHaveText(count);
      }));
    });
  });

  [tags[4], tags[9], tags[12]].forEach(data => {
    test(`should show nothing found when searching tags with ${data}`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await page.getByText('Select tags').click();
      await page.locator(`#${data}-tag`).setChecked(true, {force: true});
      await page.mouse.click(0, 0); // close modal

      await expect(page.locator('#nothing-found')).toBeVisible();
    });
  });

  test('should test uncheck all button in tags modal', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await page.getByText('Select tags').click();

    await Promise.all(tags.map(async(tag) => {
      await page.locator(`#${tag}-tag`).setChecked(true, {force: true});
      await expect(page.locator(`#${tag}-tag`)).toBeChecked();
      await expect(page.locator('#selected-tags-list')).toContainText(tag);
    }));
    await page.locator('#uncheck-button').click();
    await Promise.all(tags.map(async(tag) => {
      await expect(page.locator(`#${tag}-tag`)).not.toBeChecked();
      await expect(page.locator('#selected-tags-list')).not.toBeVisible();
    }));
  });

  [
    {selectedTags: [tags[2], tags[3]], expectedPedigreeCounts: ['500', '106']},
    {selectedTags: [tags[0], tags[3], tags[15]], expectedPedigreeCounts: ['128', '107', '106']},
    {selectedTags: [tags[3], tags[8], tags[13], tags[14]], expectedPedigreeCounts: ['877', '789']}
  ].forEach(data => {
    test(`should select tags ${data.selectedTags.join()} and check pedigrees`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await page.getByText('Select tags').click();

      await Promise.all(data.selectedTags.map(async(tag) => {
        await page.locator(`#${tag}-tag`).setChecked(true, {force: true});
        await expect(page.locator('#selected-tags-list')).toContainText(tag);
      }));
      await page.mouse.click(0, 0); // close modal

      await expect(page.locator('.pedigree-cell')).toHaveCount(data.expectedPedigreeCounts.length);
      await Promise.all(data.expectedPedigreeCounts.map(async(count, i) => {
        await expect(page.locator('.pedigree-cell').nth(i)).toHaveText(count);
      }));
    });
  });

  [
    {selectedTags: [tags[5], tags[9]], expectedPedigreeCounts: []},
    {selectedTags: [tags[3], tags[7], tags[8], tags[13], tags[14]], expectedPedigreeCounts: []}
  ].forEach(data => {
    test(`should select tags ${data.selectedTags.join()} and check if nothing found is shown`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await page.getByText('Select tags').click();

      await Promise.all(data.selectedTags.map(async(tag) => {
        await page.locator(`#${tag}-tag`).setChecked(true, {force: true});
        await expect(page.locator('#selected-tags-list')).toContainText(tag);
      }));
      await page.mouse.click(0, 0); // close modal

      await expect(page.locator('#nothing-found')).toBeVisible();
    });
  });

  test('should check pedigree chart modal content', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await page.locator('.pedigree-cell').first().click();

    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.locator('#modal-pedigree-container')).toBeVisible();
    await expect(page.locator('#modal-family-count')).toBeVisible();
    await expect(page.locator('.modal-content >> #download-button')).toBeVisible();
    await expect(page.locator('#family-ids-list > div')).not.toBeEmpty();

    await page.mouse.click(0, 0); // close modal
    await expect(page.locator('.modal-content')).not.toBeVisible();
    await expect(page.locator('#modal-pedigree-container')).not.toBeVisible();
    await expect(page.locator('#modal-family-count')).not.toBeVisible();
    await expect(page.locator('.modal-content >> #download-button')).not.toBeVisible();
    await expect(page.locator('#family-ids-list > div')).not.toBeVisible();
  });

  test('should check the count of pedigree chart family ids', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await page.locator('.pedigree-cell').nth(2).click();
    const count = parseInt(await page.locator('#modal-family-count').textContent(), 10);
    const text = await page.locator('#family-ids-list > div').textContent();
    const ids = text.split(',');
    expect(count).toEqual(ids.length);
  });
});

test.describe('Variant reports download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.getByText(utils.datasetIds.iossifov2014, {exact: true}).click();
    await page.getByText('Dataset Statistics').click();
  });

  [
    {index: 0, name: 'first', columnsToCheck: ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role']},
    {index: 1, name: 'second', columnsToCheck: ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role']},
    {index: 5, name: 'fifth', columnsToCheck: ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role']}
  ].forEach(cell => {
    test(`should download family counters report from ${cell.name} pedigree modal`, async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await expect(page.locator('#families-by-pedigree')).toBeVisible();
      await page.locator('.pedigree-cell').nth(cell.index).click();

      let downloadPromise = page.waitForEvent('download');
      downloadPromise = page.waitForEvent('download');

      await page.locator('.modal-content >> #download-button').click();
      const download = await downloadPromise;

      const fixtureData = scanCSV(await download.path(), {sep: '\t'});
      const downloadData = scanCSV(`playwright/fixtures/variant-reports/families${cell.index}.ped`, {sep: '\t'});
      const fixtureFrame = await fixtureData.select(cell.columnsToCheck).collect();
      const downloadFrame = await downloadData.select(cell.columnsToCheck).collect();
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  test('downloading all families in families by number', async({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    await page.locator('.download-link').click();
    const download = await downloadPromise;
    const columnsToCheck = ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role'];

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('playwright/fixtures/variant-reports/families-all.ped', {sep: '\t'});
    const fixtureFrame = await fixtureData.select(columnsToCheck).collect();
    const downloadFrame = await downloadData.select(columnsToCheck).collect();
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('downloading in families by pedigree', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await page.getByText('Select tags').click();
    await page.getByText('tag_trio_family').click();
    await page.keyboard.press('Escape');

    const downloadPromise = page.waitForEvent('download');
    await page.locator('#download-button').click();
    const download = await downloadPromise;

    const columnsToCheck = ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role'];

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('playwright/fixtures/variant-reports/families-pedigrees.ped', {sep: '\t'});
    const fixtureFrame = await fixtureData.select(columnsToCheck).collect();
    const downloadFrame = await downloadData.select(columnsToCheck).collect();
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});

test.describe('Variant reports Iossifov count tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.getByText(utils.datasetIds.iossifov2014, {exact: true}).click();
    await page.getByText('Dataset Statistics').click();
  });

  [
    {rowIndex: 0, roleId: 'mom', expectedCounts: ['0', '2516', '2516']},
    {rowIndex: 1, roleId: 'dad', expectedCounts: ['2516', '0', '2516']},
    {rowIndex: 2, roleId: 'proband', expectedCounts: ['2166', '341', '2507']},
    {rowIndex: 3, roleId: 'sibling', expectedCounts: ['899', '1011', '1910']}
  ].forEach(data => {
    test(`should display the correct numbers in families by numbers of role - 
      ${data.roleId} pedigree modal`, async({ page }) => {
      await page.locator('#families-by-number-select').selectOption('Role');
      await expect(page.locator('div#families-by-number-div tbody th').nth(data.rowIndex)).toHaveText(data.roleId);

      await Promise.all(data.expectedCounts.map(async(el, i) => {
        await expect(page.locator('div#families-by-number-div td').nth((data.rowIndex * 3) + i)).toHaveText(el);
      }));
    });
  });

  [
    {rowIndex: 0, effectType: 'LGDs', expectedCounts: ['393, 0.157(366, 15%)', '180, 0.094(169, 9%)']},
    {rowIndex: 2, effectType: 'UTRs', expectedCounts: ['244, 0.097(237, 9%)', '154, 0.081(144, 8%)']},
    {rowIndex: 6, effectType: 'Missense', expectedCounts: ['1680, 0.67(1185, 47%)', '1149, 0.602(843, 44%)']},
    {rowIndex: 12, effectType: 'Intron', expectedCounts: ['821, 0.327(671, 27%)', '558, 0.292(464, 24%)']}
  ].forEach(data => {
    test('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" role table', async({ page }) => {
      await page.getByText('De Novo variants').click();
      await page.locator('#denovo-variants-select').selectOption('Role');
      await Promise.all(data.expectedCounts.map(async(el) => {
        await expect(page.locator('#denovo-variants-div tr').nth(data.rowIndex)).toContainText(data.effectType);
        await expect(page.locator('#denovo-variants-div tr').nth(data.rowIndex)).toContainText(el);
      }));
    });
  });

  [
    {rowIndex: 0, effectType: 'LGDs', expectedCounts: ['393, 0.157(366, 15%)', '180, 0.094(169, 9%)']},
    {rowIndex: 2, effectType: 'UTRs', expectedCounts: ['244, 0.097(237, 9%)', '154, 0.081(144, 8%)']},
    {rowIndex: 6, effectType: 'Missense', expectedCounts: ['1680, 0.67(1185, 47%)', '1149, 0.602(843, 44%)']},
    {rowIndex: 12, effectType: 'Intron', expectedCounts: ['821, 0.327(671, 27%)', '558, 0.292(464, 24%)']}
  ].forEach(data => {
    test('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" status table', async({ page }) => {
      await page.getByText('De Novo variants').click();
      await page.locator('#denovo-variants-select').selectOption('Affected Status');
      await Promise.all(data.expectedCounts.map(async(el) => {
        await expect(page.locator('#denovo-variants-div tr').nth(data.rowIndex)).toContainText(data.effectType);
        await expect(page.locator('#denovo-variants-div tr').nth(data.rowIndex)).toContainText(el);
      }));
    });
  });
});