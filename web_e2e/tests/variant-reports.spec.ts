import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { VariantReports } from './components/variant-reports.component';
import { Datasets } from './components/datasets.component';
import { Header } from './components/header.component';

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

async function navigateToDatasetStatistics(page: import('@playwright/test').Page): Promise<void> {
  const datasets = new Datasets(page);
  const header = new Header(page);
  await header.navLink('Datasets').click();
  await datasets.dropdownButton.click();
  await page.getByText(utils.datasetIds.iossifov2014Liftover, {exact: true}).click();
  await datasets.toolLink('Dataset Statistics').click();
}

test.describe('Variant reports tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await navigateToDatasetStatistics(page);
  });

  test('should display the correct elements in the families by number tab', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by number').click();
    await expect(variantReports.downloadTotalFamilies).toBeVisible();
    await expect(variantReports.familiesByNumberSelect).toBeVisible();
    await expect(variantReports.familiesByNumberDiv).toBeVisible();

    await variantReports.tab('De Novo variants').click();
    await expect(variantReports.downloadTotalFamilies).not.toBeVisible();
    await expect(variantReports.familiesByNumberSelect).not.toBeVisible();
    await expect(variantReports.familiesByNumberDiv).not.toBeVisible();
  });

  test('should display the correct elements in the families by pedigree tab', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();
    await expect(variantReports.familiesByPedigreeSelect).toBeVisible();
    await expect(variantReports.downloadButton).toBeVisible();
    await expect(variantReports.familiesByPedigreeDiv).toBeVisible();
    await expect(variantReports.selectTags).toBeVisible();

    await variantReports.tab('De Novo variants').click();
    await expect(variantReports.familiesByPedigreeSelect).not.toBeVisible();
    await expect(variantReports.downloadButton).not.toBeVisible();
    await expect(variantReports.familiesByPedigreeDiv).not.toBeVisible();
    await expect(variantReports.selectTags).not.toBeVisible();
  });

  test('should display the correct elements in the families by denovo tab', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('De Novo variants').click();
    await expect(variantReports.denovoVariantsSelect).toBeVisible();
    await expect(variantReports.denovoVariantsLegendReport).toBeVisible();
    await expect(variantReports.denovoVariantsDiv).toBeVisible();

    await variantReports.tab('Families by number').click();
    await expect(variantReports.denovoVariantsSelect).not.toBeVisible();
    await expect(variantReports.denovoVariantsLegendReport).not.toBeVisible();
    await expect(variantReports.denovoVariantsDiv).not.toBeVisible();
  });

  [
    {option: 'Affected Status', legendElements: ['affected', 'unaffected']},
    {option: 'Role', legendElements: ['mom', 'dad', 'proband', 'sibling']},
    {option: 'Phenotype', legendElements: ['autism', 'unaffected']}
  ].forEach(data => {
    test('should check content of the legend for ' + data.option +
      ' option in the families by pedigree tab', async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('Families by pedigree').click();
      await expect(variantReports.expandLegendButton).toBeVisible();
      await expect(variantReports.legend).not.toBeVisible();
      await variantReports.familiesByPedigreeSelect.selectOption(data.option);

      await variantReports.expandLegendButton.click();
      await expect(variantReports.legend).toBeVisible();

      await expect(variantReports.legendItems).toHaveCount(data.legendElements.length);

      await expect(variantReports.legend).toContainText(data.legendElements.join(''));

      await variantReports.expandLegendButton.click();
      await expect(variantReports.legend).not.toBeVisible();
    });
  });

  test('should check content of the select in the families by pedigree tab', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();

    await expect(variantReports.familiesByPedigreeSelect.locator('option')).toHaveCount(3);

    const option1 = await variantReports.familiesByPedigreeSelect.locator('option').nth(0).textContent();
    expect(['Affected Status', 'Role', 'Phenotype']).toContain(option1);

    const option2 = await variantReports.familiesByPedigreeSelect.locator('option').nth(1).textContent();
    expect(['Affected Status', 'Role', 'Phenotype']).toContain(option2);

    const option3 = await variantReports.familiesByPedigreeSelect.locator('option').nth(2).textContent();
    expect(['Affected Status', 'Role', 'Phenotype']).toContain(option3);
  });

  test('should open, close and check content for selecting tags', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();
    await expect(variantReports.selectTags).toBeVisible();
    await expect(variantReports.tagsModalContent).not.toBeVisible();

    await variantReports.selectTags.click();
    await expect(variantReports.tagsModalContent).toBeVisible();
    await expect(variantReports.andButton).toBeVisible();
    await expect(variantReports.orButton).toBeVisible();
    await expect(page.getByText('Choose mode: ')).toBeVisible();
    await expect(variantReports.clearFilters).toBeVisible();
    await expect(variantReports.tagList).toBeVisible();

    await expect(variantReports.tagList)
      .toContainText('add_circleremove_circle' + tags.join('add_circleremove_circle'));

    await page.mouse.click(0, 0);
    await expect(variantReports.tagsModalContent).not.toBeVisible();
  });

  test('should test clear all filters', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();
    await variantReports.selectTags.click();

    await variantReports.tagAdd(tags[2]).click();
    await expect(variantReports.selectedTagsList).toContainText(tags[2]);
    await expect(variantReports.tagAdd(tags[2])).toHaveCSS('color', 'rgb(0, 128, 0)');

    await variantReports.tagRemove(tags[7]).click();
    await expect(variantReports.selectedTagsList).toContainText('not ' + tags[7]);
    await expect(variantReports.tagRemove(tags[7])).toHaveCSS('color', 'rgb(255, 0, 0)');

    await variantReports.tagRemove(tags[10]).click();
    await expect(variantReports.selectedTagsList).toContainText('not ' + tags[10]);
    await expect(variantReports.tagRemove(tags[10])).toHaveCSS('color', 'rgb(255, 0, 0)');

    await variantReports.tagAdd(tags[12]).click();
    await expect(variantReports.selectedTagsList).toContainText(tags[12]);
    await expect(variantReports.tagAdd(tags[12])).toHaveCSS('color', 'rgb(0, 128, 0)');

    await variantReports.clearFilters.click();
    await expect(variantReports.tagAdd(tags[2])).not.toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(variantReports.tagAdd(tags[7])).not.toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(variantReports.tagAdd(tags[10])).not.toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(variantReports.tagAdd(tags[12])).not.toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(variantReports.selectedTagsList).not.toBeVisible();
  });

  [
    {selectedTags: [tags[14]], deselectedTags: [tags[2]], expectedPedigreeCounts: ['877', '789']},
    {selectedTags: [tags[8], tags[13]], deselectedTags: [tags[14]], expectedPedigreeCounts: ['128', '107']}
  ].forEach(data => {
    test(`should select tags ${data.selectedTags.join()} and
      deselect tags ${data.deselectedTags.join()}`, async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('Families by pedigree').click();
      await variantReports.selectTags.click();

      for (const tag of data.selectedTags) {
        // eslint-disable-next-line no-await-in-loop
        await variantReports.tagAdd(tag).click();
        // eslint-disable-next-line no-await-in-loop
        await expect(variantReports.selectedTagsList).toContainText(tag);
      }

      for (const tag of data.deselectedTags) {
        // eslint-disable-next-line no-await-in-loop
        await variantReports.tagRemove(tag).click();
        // eslint-disable-next-line no-await-in-loop
        await expect(variantReports.selectedTagsList).toContainText('not ' + tag);
      }
      await page.mouse.click(0, 0); // close modal

      await expect(variantReports.pedigreeCells).toHaveCount(data.expectedPedigreeCounts.length);
      await Promise.all(data.expectedPedigreeCounts.map(async(count, i) => {
        await expect(variantReports.pedigreeCells.nth(i)).toHaveText(count);
      }));
    });
  });

  [
    {selectedTags: [tags[8], tags[14]], deselectedTags: [tags[6], tags[10]]},
    {selectedTags: [tags[5], tags[9]], deselectedTags: [tags[1], tags[7]]},
  ].forEach(data => {
    test(`should select tags ${data.selectedTags.join()} and
      deselect tags ${data.deselectedTags.join()} and check if nothing found is shown`, async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('Families by pedigree').click();
      await variantReports.selectTags.click();

      for (const tag of data.selectedTags) {
        // eslint-disable-next-line no-await-in-loop
        await variantReports.tagAdd(tag).click();
        // eslint-disable-next-line no-await-in-loop
        await expect(variantReports.selectedTagsList).toContainText(tag);
      }

      for (const tag of data.deselectedTags) {
        // eslint-disable-next-line no-await-in-loop
        await variantReports.tagRemove(tag).click();
        // eslint-disable-next-line no-await-in-loop
        await expect(variantReports.selectedTagsList).toContainText('not ' + tag);
      }

      await page.mouse.click(0, 0); // close modal

      await expect(variantReports.nothingFound).toBeVisible();
    });
  });

  [
    {selectedTag: tags[14], deselectedTag: tags[1], expectedPedigreeCounts: ['877', '789', '500', '106', '6', '3']},
    {selectedTag: tags[2], deselectedTag: tags[3], expectedPedigreeCounts: ['500', '106', '6', '3']},
  ].forEach(data => {
    test(`should check Or mode with selected ${data.selectedTag}
      and deselected ${data.deselectedTag}`, async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('Families by pedigree').click();
      await variantReports.selectTags.click();
      await variantReports.orButton.click();


      await variantReports.tagAdd(data.selectedTag).click();
      await expect(variantReports.selectedTagsList).toContainText(data.selectedTag);

      await variantReports.tagRemove(data.deselectedTag).click();
      await expect(variantReports.selectedTagsList).toContainText('not ' + data.deselectedTag);

      await page.mouse.click(0, 0); // close modal

      await expect(variantReports.pedigreeCells).toHaveCount(data.expectedPedigreeCounts.length);
      await Promise.all(data.expectedPedigreeCounts.map(async(count, i) => {
        await expect(variantReports.pedigreeCells.nth(i)).toHaveText(count);
      }));
    });
  });

  [
    {selectedTag: tags[4], deselectedTag: tags[0]},
    {selectedTag: tags[17], deselectedTag: tags[11]},
  ].forEach(data => {
    test(`should check Or mode with selected ${data.selectedTag}
    and deselected ${data.deselectedTag} and check if nothing found is shown`, async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('Families by pedigree').click();
      await variantReports.selectTags.click();

      await variantReports.tagAdd(data.selectedTag).click();
      await expect(variantReports.selectedTagsList).toContainText(data.selectedTag);

      await variantReports.tagRemove(data.deselectedTag).click();
      await expect(variantReports.selectedTagsList).toContainText('not ' + data.deselectedTag);

      await variantReports.orButton.click();

      await page.mouse.click(0, 0); // close modal

      await expect(variantReports.nothingFound).toBeVisible();
    });
  });

  test('should check pedigree chart modal content', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();
    await variantReports.pedigreeCells.first().click();

    await expect(variantReports.modalContent).toBeVisible();
    await expect(variantReports.modalPedigreeContainer).toBeVisible();
    await expect(variantReports.modalFamilyCount).toBeVisible();
    await expect(variantReports.modalDownloadButton).toBeVisible();
    await expect(variantReports.familyIdsList).not.toBeEmpty();

    await page.mouse.click(0, 0); // close modal
    await expect(variantReports.modalContent).not.toBeVisible();
    await expect(variantReports.modalPedigreeContainer).not.toBeVisible();
    await expect(variantReports.modalFamilyCount).not.toBeVisible();
    await expect(variantReports.modalDownloadButton).not.toBeVisible();
    await expect(variantReports.familyIdsList).not.toBeVisible();
  });

  test('should check the count of pedigree chart family ids', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();
    await variantReports.pedigreeCells.nth(2).click();
    const count = parseInt(await variantReports.modalFamilyCount.textContent(), 10);
    const text = await variantReports.familyIdsList.textContent();
    const ids = text.split(',');
    expect(count).toEqual(ids.length);
  });

  test('if Rate of de Novo variants tab is not visible when selected study has no denovo', async({ page }) => {
    const variantReports = new VariantReports(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.vcfHelloWorld, 'Dataset Statistics');
    await expect(variantReports.tab('Rate of de Novo variants')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Dataset Statistics');
    await expect(variantReports.tab('Rate of de Novo variants')).toBeVisible();
  });
});

test.describe('Variant reports download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await navigateToDatasetStatistics(page);
  });

  [
    {index: 0, name: 'first', columnsToCheck: ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role']},
    {index: 1, name: 'second', columnsToCheck: ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role']},
    {index: 5, name: 'fifth', columnsToCheck: ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role']}
  ].forEach(cell => {
    test(`should download family counters report from ${cell.name} pedigree modal`, async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('Families by pedigree').click();
      await expect(variantReports.familiesByPedigree).toBeVisible();
      await variantReports.pedigreeCells.nth(cell.index).click();

      let downloadPromise = page.waitForEvent('download');
      downloadPromise = page.waitForEvent('download');

      await variantReports.modalDownloadButton.click();
      const download = await downloadPromise;

      const fixtureData = scanCSV(await download.path(), {sep: '\t'});
      const downloadData = scanCSV(`fixtures/variant-reports/families${cell.index}.ped`, {sep: '\t'});
      const fixtureFrame = (await fixtureData.select(cell.columnsToCheck).collect()).sort('familyId');
      const downloadFrame = (await downloadData.select(cell.columnsToCheck).collect()).sort('familyId');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  test('downloading all families in families by number', async({ page }) => {
    const variantReports = new VariantReports(page);
    const downloadPromise = page.waitForEvent('download');
    await variantReports.downloadLink.click();
    const download = await downloadPromise;
    const columnsToCheck = ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role'];

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('fixtures/variant-reports/families-all.ped', {sep: '\t'});
    const fixtureFrame = await fixtureData.select(columnsToCheck).collect();
    const downloadFrame = await downloadData.select(columnsToCheck).collect();
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('downloading in families by pedigree', async({ page }) => {
    const variantReports = new VariantReports(page);
    await variantReports.tab('Families by pedigree').click();
    await variantReports.selectTags.click();
    await variantReports.tagAdd('tag_trio_family').click();
    await page.keyboard.press('Escape');

    const downloadPromise = page.waitForEvent('download');
    await variantReports.downloadButton.click();
    const download = await downloadPromise;

    const columnsToCheck = ['familyId', 'personId', 'momId', 'dadId', 'sex', 'status', 'role'];

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('fixtures/variant-reports/families-pedigrees.ped', {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(columnsToCheck).collect()).sort('familyId');
    const downloadFrame = (await downloadData.select(columnsToCheck).collect()).sort('familyId');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});

test.describe('Variant reports Iossifov count tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await navigateToDatasetStatistics(page);
  });

  [
    {rowIndex: 0, roleId: 'mom', expectedCounts: ['0', '2516', '2516']},
    {rowIndex: 1, roleId: 'dad', expectedCounts: ['2516', '0', '2516']},
    {rowIndex: 2, roleId: 'proband', expectedCounts: ['2166', '341', '2507']},
    {rowIndex: 3, roleId: 'sibling', expectedCounts: ['899', '1011', '1910']}
  ].forEach(data => {
    test(`should display the correct numbers in families by numbers of role -
      ${data.roleId} pedigree modal`, async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.familiesByNumberSelect.selectOption('Role');
      await expect(variantReports.familiesByNumberDiv.locator('tbody th').nth(data.rowIndex)).toHaveText(data.roleId);

      await Promise.all(data.expectedCounts.map(async(el, i) => {
        await expect(variantReports.familiesByNumberDiv.locator('td').nth((data.rowIndex * 3) + i)).toHaveText(el);
      }));
    });
  });

  [
    {rowIndex: 0, effectType: 'LGDs', expectedCounts: ['68, 0.027(68, 3%)25, 0.013(24, 1%)']},
    {rowIndex: 2, effectType: 'UTRs', expectedCounts: ['62, 0.025(62, 2%)', '43, 0.023(43, 2%)']},
    {rowIndex: 6, effectType: 'Missense', expectedCounts: ['274, 0.109(240, 10%)', '189, 0.099(179, 9%)']},
    {rowIndex: 10, effectType: 'Intron', expectedCounts: ['141, 0.056(136, 5%)', '99, 0.052(96, 5%)']}
  ].forEach(data => {
    test('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" role table', async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('De Novo variants').click();
      await variantReports.denovoVariantsSelect.selectOption('Role');
      await Promise.all(data.expectedCounts.map(async(el) => {
        await expect(variantReports.denovoVariantsDiv.locator('tr').nth(data.rowIndex)).toContainText(data.effectType);
        await expect(variantReports.denovoVariantsDiv.locator('tr').nth(data.rowIndex)).toContainText(el);
      }));
    });
  });

  [
    {rowIndex: 0, effectType: 'LGDs', expectedCounts: ['68, 0.027(68, 3%)25, 0.013(24, 1%)']},
    {rowIndex: 2, effectType: 'UTRs', expectedCounts: ['62, 0.025(62, 2%)', '43, 0.023(43, 2%)']},
    {rowIndex: 6, effectType: 'Missense', expectedCounts: ['274, 0.109(240, 10%)', '189, 0.099(179, 9%)']},
    {rowIndex: 10, effectType: 'Intron', expectedCounts: ['141, 0.056(136, 5%)', '99, 0.052(96, 5%)']}
  ].forEach(data => {
    test('should display the correct numbers for ' + data.effectType +
       ' effectType in the "Denovo variants of:" status table', async({ page }) => {
      const variantReports = new VariantReports(page);
      await variantReports.tab('De Novo variants').click();
      await variantReports.denovoVariantsSelect.selectOption('Affected Status');
      await Promise.all(data.expectedCounts.map(async(el) => {
        await expect(variantReports.denovoVariantsDiv.locator('tr').nth(data.rowIndex)).toContainText(data.effectType);
        await expect(variantReports.denovoVariantsDiv.locator('tr').nth(data.rowIndex)).toContainText(el);
      }));
    });
  });
});
