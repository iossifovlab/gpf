import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';
import { scanCSV } from 'nodejs-polars';
import { GenotypeBrowserPage } from './pages/genotype-browser.page';

test.describe('Genotype browser tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display filters blocks and buttons', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.tablePreviewButton).toBeVisible();
    await expect(genotypeBrowser.shareSaveButton).toBeVisible();
    await expect(genotypeBrowser.downloadButton).toBeVisible();

    await expect(genotypeBrowser.regions.root).toBeVisible();
    await expect(genotypeBrowser.genes.root).toBeVisible();
    await expect(genotypeBrowser.genotypeBlock.root).toBeVisible();
    await expect(genotypeBrowser.genomicScores.root).toBeVisible();
    await expect(genotypeBrowser.familyFilters.root).toBeVisible();
    await expect(genotypeBrowser.personFilters.root).toBeVisible();
    await expect(genotypeBrowser.uniqueFamilyVariantsFilter).toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(genotypeBrowser.uniqueFamilyVariantsFilter).toBeVisible();
  });

  test('should hide table preview results after changing a filter', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.previewTable).toBeVisible();

    await genotypeBrowser.genotypeBlock.presentInChild.label('sibling only').click();
    await expect(genotypeBrowser.previewTable).not.toBeVisible();
  });

  test('should load query after filtering with scores and family and person filters', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore(
      'SFARI Gene Score - Evidence strength supporting a gene\'s association with autism'
    );

    await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await genomicScores.selectScore(clinsig);

    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('Pathogenic');
    const pathogenic = genomicScores.valueOption(/^Pathogenic \(/);
    await expect(pathogenic).toHaveCount(1);
    await pathogenic.click();
    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('Likely_pathogenic');
    const likelyPathogenic = genomicScores.valueOption(/^Likely_pathogenic \(/);
    await expect(likelyPathogenic).toHaveCount(1);
    await likelyPathogenic.click();
    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('Uncertain_significance');
    const uncertainSig = genomicScores.valueOption(/^Uncertain_significance \(/);
    await expect(uncertainSig).toHaveCount(1);
    await uncertainSig.click();

    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await genotypeBrowser.familyFilters.measuresTextbox.click();
    await genotypeBrowser.familyFilters.phenoMeasures.measureOption('instrument_1.measure_5').click();

    await genotypeBrowser.personFilters.openPhenoMeasuresTab();
    await genotypeBrowser.personFilters.measuresTextbox.click();
    await genotypeBrowser.familyFilters.phenoMeasures.measureOption('instrument_1.measure_5').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('7 variants selected', { timeout: 120000 });

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genotypeBrowser.genes.geneScoresPanel).toBeVisible();
    await expect(genomicScores.scores).toBeVisible();
    await expect(genotypeBrowser.familyFilters.root.locator('svg')).toBeVisible();
    await expect(genotypeBrowser.personFilters.root.locator('svg')).toBeVisible();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('7 variants selected', { timeout: 120000 });
  });
});

test.describe('Genotype browser table preview result tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
  });

  [
    {study: datasetIds.helloWorldGenotypes, count: '10'},
    {study: datasetIds.denovoHelloWorld, count: '10'},
    {study: datasetIds.vcfHelloWorld, count: '15'},
    {study: datasetIds.iossifov2014Liftover, count: '8'},
    {study: datasetIds.multiLiftover, count: '0'}
  ].forEach(data => {
    test('should display the correct overview paragraph ' +
    'when gene symbol is "CHD8" at /' + data.study + '/browser', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');
      await genotypeBrowser.genes.openGeneSymbolsTab();
      await genotypeBrowser.genes.geneSymbols.textbox.focus();
      await page.keyboard.type('CHD8');
      await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();

      await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {region: 'chr1:101806080-125000000', count: '7'},
    {region: 'chr1:1592000-15929267', count: '5'},
    {region: 'chrX:70000000-74000000', count: '2'}
  ].forEach(data => {
    test('should display the correct overview paragraph' +
    ' when regions filter is "' + data.region + '" at /iossifov_2014_liftover/browser', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
      await genotypeBrowser.regions.regionsFilterToggle.click();
      await genotypeBrowser.regions.textarea.focus();
      await page.keyboard.type(data.region);
      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.denovoHelloWorld,
      affectedStatus: 'affected',
      count: '61'
    },
    {
      study: datasetIds.vcfHelloWorld,
      affectedStatus: 'affected',
      count: '19'
    },
    {
      study: datasetIds.vcfHelloWorld,
      affectedStatus: 'unaffected',
      count: '27'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when ' +
    'affected status - ' + data.affectedStatus + ' is checked at /' + data.study + '/browser', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      const pedigreeSelector = genotypeBrowser.genotypeBlock.pedigreeSelector;
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await pedigreeSelector.openAffectedStatus();
      await pedigreeSelector.noneButton.click();
      await pedigreeSelector.label(data.affectedStatus).click();

      await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {childGender: 'male', count: '57'},
    {childGender: 'female', count: '35'},
    {childGender: 'unspecified', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph when ' +
        'child gender is ' + data.childGender, async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

      await genotypeBrowser.genotypeBlock.gender.noneButton.click();
      await genotypeBrowser.genotypeBlock.gender.genderIcon(data.childGender).click();

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {variantType: 'sub', count: '48'},
    {variantType: 'ins', count: '15'},
    {variantType: 'del', count: '29'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph when only ' +
    data.variantType + ' variant type checkbox is checked', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

      await genotypeBrowser.genotypeBlock.variantTypes.button('None').click();
      await genotypeBrowser.genotypeBlock.variantTypes.label(data.variantType).click();

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {effectType: 'All', count: '27'},
    {effectType: 'LGDs', count: '0'},
    {effectType: 'Nonsynonymous', count: '11'},
    {effectType: 'Coding', count: '15'},
    {effectType: 'UTRs', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph' +
        ' where effect types are ' + data.effectType, async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      const effectTypes = genotypeBrowser.genotypeBlock.effectTypes;
      await utils.navigateToDatasetPage(page, datasetIds.vcfHelloWorld, 'Genotype browser');

      await effectTypes.clickButton('None');
      await effectTypes.clickButton(data.effectType);

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.multiLiftover,
      inheritanceType: 'mendelian',
      count: '2'
    },
    {
      study: datasetIds.denovoHelloWorld,
      inheritanceType: 'denovo',
      count: '61'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when ' +
    'inheritance types are ' + data.inheritanceType + ' at /' + data.study + '/browser', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      const inheritanceTypes = genotypeBrowser.genotypeBlock.inheritanceTypes;
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await inheritanceTypes.button('None').click();
      await inheritanceTypes.label(data.inheritanceType).click();

      await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {familyId: 'f1', count: '28'},
    {familyId: 'f2', count: '23'},
    {familyId: 'f3', count: '0'},
  ].forEach(data => {
    test('should display the correct overview paragraph when family id is "' + data.familyId + '"', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');

      await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

      await genotypeBrowser.familyFilters.openFamilyIds();
      await genotypeBrowser.familyFilters.familyIds.textarea.pressSequentially(data.familyId);

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.iossifov2014Liftover,
      geneSymbol: 'POGZ',
      effectType: 'LGDs',
      overviewParagraph: '2 variants selected'
    },
    {
      study: datasetIds.iossifov2014Liftover,
      geneSymbol: 'MEGF6',
      effectType: 'LGDs',
      overviewParagraph: '1 variant selected'
    },
    {
      study: datasetIds.iossifov2014Liftover,
      geneSymbol: 'MEGF6',
      effectType: 'All',
      overviewParagraph: '1 variant selected'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when effect types are ' +
        data.effectType + ' and gene symbol is "' + data.geneSymbol +
        '" at /' + data.study + '/browser', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      const effectTypes = genotypeBrowser.genotypeBlock.effectTypes;
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await genotypeBrowser.genes.openGeneSymbolsTab();
      await genotypeBrowser.genes.geneSymbols.textbox.focus();
      await page.keyboard.type(data.geneSymbol);
      await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();

      await effectTypes.clickButton('None');
      await effectTypes.clickButton(data.effectType);


      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(data.overviewParagraph);
    });
  });

  test('should display "2 variants selected" in overview paragraph ' +
  'when family id is 11057 at /iossifov_2014/browser', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

    await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');
    await genotypeBrowser.familyFilters.openFamilyIds();
    await genotypeBrowser.familyFilters.familyIds.textarea.pressSequentially('11057');

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('2 variants selected');
  });

  test('should display "0 variants selected" in overview paragraph when the gene sets is ' +
  'GO Terms - GO:0016917 and effect type LGDs at /iossifov_2014/browser', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneSets = genotypeBrowser.genes.geneSets;
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

    await genotypeBrowser.genotypeBlock.effectTypes.clickButton('LGDs');

    const goTerm =
      'GO:0016917-GABA_receptor_activity (23): https://www.ebi.ac.uk/QuickGO/term/GO:0016917';
    await genotypeBrowser.genes.openGeneSets();
    await geneSets.collectionSelect.click();
    await geneSets.collectionSelect.selectOption('GO Terms');
    await geneSets.searchBox.click();
    await page.keyboard.type('GO:0016917');
    await geneSets.optionByTitle(goTerm).waitFor();
    await geneSets.optionByText(goTerm).click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('0 variants selected');
  });

  [
    {
      effectTypes: ['missense'],
      count: '0'
    },
    {
      effectTypes: ['missense', 'synonymous'],
      count: '0'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when gene sets is GO Terms'+
    ' - GO:0016917 and effect types are ' + data.effectTypes.toString() +
    ' at /iossifov2014Liftover/browser', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      const geneSets = genotypeBrowser.genes.geneSets;
      const effectTypes = genotypeBrowser.genotypeBlock.effectTypes;
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

      const goTerm =
        'GO:0016917-GABA_receptor_activity (23): https://www.ebi.ac.uk/QuickGO/term/GO:0016917';
      await genotypeBrowser.genes.openGeneSets();
      await geneSets.collectionSelect.click();
      await geneSets.collectionSelect.selectOption('GO Terms');
      await geneSets.searchBox.click();
      await page.keyboard.type('GO:0016917');
      await geneSets.optionByTitle(goTerm).waitFor();
      await geneSets.optionByText(goTerm).click();

      await effectTypes.clickButton('None');

      for (const type of data.effectTypes) {
        // eslint-disable-next-line no-await-in-loop
        await effectTypes.label(type).click();
      }

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.variantsCount).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {familyId: 'f1', values: {age: '166.33975219726562', iq: '124.9118881225586'}},
    {familyId: 'f2', values: {age: '111.53800201416016', iq: '118.6941146850586'}},
  ].forEach(data => {
    test('should display the correct age and iq values in the measures column for "'
    + data.familyId + '" family', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      await utils.navigateToDatasetPage(page, datasetIds.vcfHelloWorld, 'Genotype browser');

      await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

      await genotypeBrowser.familyFilters.openFamilyIds();
      await genotypeBrowser.familyFilters.familyIds.textarea.pressSequentially(data.familyId);

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.tableViewCell.nth(0)).toContainText(data.values.age);
      await expect(genotypeBrowser.tableViewCell.nth(1)).toContainText(data.values.iq);
    });
  });

  test('should display the correct overview paragraph with ' +
  'denovo inheritance types, affected only, 5\'UTR', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genotypeBlock = genotypeBrowser.genotypeBlock;
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

    await genotypeBlock.pedigreeSelector.openAffectedStatus();
    await genotypeBlock.pedigreeSelector.noneButton.click();
    await genotypeBlock.pedigreeSelector.label('affected').click();

    await genotypeBlock.inheritanceTypes.button('None').click();
    await genotypeBlock.inheritanceTypes.label('denovo').click();

    await genotypeBlock.effectTypes.clickButton('None');
    await genotypeBlock.effectTypes.clickLabel('5\'UTR');

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('23 variants selected');
  });

  test('should load query, click table preview and check if table is visible repeatedly', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    await genotypeBrowser.genes.openGeneSymbolsTab();

    for (let i = 0; i < 5; i++) {
      /* eslint-disable no-await-in-loop */
      await genotypeBrowser.genes.geneSymbols.textbox.clear();
      await genotypeBrowser.genes.geneSymbols.textbox.pressSequentially('CHD8');

      const shareLinkUrl = await genotypeBrowser.getShareLink();
      await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
      await page.goto(shareLinkUrl, {waitUntil: 'load'});

      await expect(async() => {
        await genotypeBrowser.runTablePreview();
        await expect(genotypeBrowser.previewTable).toBeVisible({timeout: 5000});
      }).toPass({intervals: [1000]});
      /* eslint-enable */
    }
  });

  test('should load query, click table preview and check if loading screen is hidden repeatedly', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    await genotypeBrowser.genes.openGeneSymbolsTab();

    for (let i = 0; i < 5; i++) {
      /* eslint-disable no-await-in-loop */
      await genotypeBrowser.genes.geneSymbols.textbox.clear();
      await genotypeBrowser.genes.geneSymbols.textbox.pressSequentially('CHD8');

      const shareLinkUrl = await genotypeBrowser.getShareLink();
      await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
      await page.goto(shareLinkUrl, {waitUntil: 'load'});

      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.overlay).not.toBeVisible();
      /* eslint-enable */
    }
  });
});

test.describe('Genotype browser download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
  });

  test('should download all effect types CHD8 iossifov variants ' +
  'and validate whether they are equal to the reference data', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneSymbolsTab();
    await genotypeBrowser.genes.geneSymbols.textbox.focus();
    await page.keyboard.type('CHD8');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();

    await genotypeBrowser.genotypeBlock.effectTypes.clickButton('All');

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();
    const download = await downloadPromise;
    const fixtureData = scanCSV(await download.path(), { sep: '\t'});
    const downloadData = scanCSV('fixtures/genotype-browser/variants-1.tsv', { sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});


test.describe('Genotype browser table tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
  });

  test('should redirect to UCSC', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.runTablePreview();

    const baseUrl = 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=';

    await page.waitForSelector('span:text("92 variants selected")');
    await genotypeBrowser.sortChild.getByText('family id').click();

    await expect(
      genotypeBrowser.variantLink(/^chr1:153665244$/).first()
    ).toHaveAttribute('href', baseUrl + 'chr1:153665244');


    await expect(
      genotypeBrowser.variantLink(/^chrX:1389485$/).first()
    ).toHaveAttribute('href', baseUrl + 'chrX:1389485');
  });

  test('should show details', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.runTablePreview();
    await page.waitForSelector('span:text("92 variants selected")');
    await genotypeBrowser.sortChild.getByText('family id').click();

    await genotypeBrowser.showDetails.first().click();
    await expect(genotypeBrowser.detailsModal).toBeVisible();
    await expect(genotypeBrowser.detailsHeaders).toHaveCount(2);
    await expect(genotypeBrowser.detailsHeaders.nth(0)).toHaveText('Family id: 14621');
    await expect(genotypeBrowser.detailsHeaders.nth(1)).toHaveText('Location: chr1:153665244');
    await expect(genotypeBrowser.detailsGrid).toBeVisible();
  });
});

test.describe('Genotype browser zygosity tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should check which filters have zygosity and if all types are selected by default', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const zygosity = genotypeBrowser.genotypeBlock.zygosity;
    await expect(zygosity.filter('pedigreeSelector')).toBeVisible();
    await expect(zygosity.checkbox('pedigreeSelector', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('pedigreeSelector', 'heterozygous')).toBeChecked();

    await expect(zygosity.filter('presentInChild')).toBeVisible();
    await expect(zygosity.checkbox('presentInChild', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInChild', 'heterozygous')).toBeChecked();

    await expect(zygosity.filter('presentInParent')).toBeVisible();
    await expect(zygosity.checkbox('presentInParent', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInParent', 'heterozygous')).toBeChecked();

    await expect(zygosity.filter('carrierGender')).toBeVisible();
    await expect(zygosity.checkbox('carrierGender', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('carrierGender', 'heterozygous')).toBeChecked();

    await expect(genotypeBrowser.genotypeBlock.effectTypes.zygosityFilter).not.toBeVisible();
    await expect(genotypeBrowser.genotypeBlock.variantTypes.zygosityFilter).not.toBeVisible();
    await expect(genotypeBrowser.genotypeBlock.inheritanceTypes.zygosityFilter).not.toBeVisible();
  });

  test('should show error message when no zygosity type is selected', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const zygosity = genotypeBrowser.genotypeBlock.zygosity;
    await expect(zygosity.selectAtLeastOneError('presentInChild')).not.toBeVisible();

    await zygosity.checkbox('presentInChild', 'homozygous').uncheck();
    await zygosity.checkbox('presentInChild', 'heterozygous').uncheck();
    await expect(zygosity.selectAtLeastOneError('presentInChild')).toBeVisible();

    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await zygosity.checkbox('presentInChild', 'heterozygous').check();
    await expect(zygosity.selectAtLeastOneError('presentInChild')).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('should check if zygosity types are loaded correctly after sharing query', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const zygosity = genotypeBrowser.genotypeBlock.zygosity;
    await zygosity.checkbox('pedigreeSelector', 'homozygous').uncheck();
    await zygosity.checkbox('presentInChild', 'heterozygous').uncheck();
    await zygosity.checkbox('presentInParent', 'homozygous').uncheck();
    await zygosity.checkbox('carrierGender', 'heterozygous').uncheck();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(zygosity.checkbox('pedigreeSelector', 'homozygous')).not.toBeChecked();
    await expect(zygosity.checkbox('pedigreeSelector', 'heterozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInChild', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInChild', 'heterozygous')).not.toBeChecked();
    await expect(zygosity.checkbox('presentInParent', 'heterozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInParent', 'homozygous')).not.toBeChecked();
    await expect(zygosity.checkbox('carrierGender', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('carrierGender', 'heterozygous')).not.toBeChecked();
  });

  test('should check if zygosity types are reset when switching tools', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const zygosity = genotypeBrowser.genotypeBlock.zygosity;
    await zygosity.checkbox('pedigreeSelector', 'homozygous').uncheck();
    await zygosity.checkbox('presentInChild', 'heterozygous').uncheck();
    await zygosity.checkbox('presentInParent', 'homozygous').uncheck();
    await zygosity.checkbox('carrierGender', 'heterozygous').uncheck();

    await genotypeBrowser.openToolLink('Enrichment Tool');
    await genotypeBrowser.openToolLink('Genotype Browser');

    await expect(zygosity.checkbox('pedigreeSelector', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInChild', 'heterozygous')).toBeChecked();
    await expect(zygosity.checkbox('presentInParent', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('carrierGender', 'heterozygous')).toBeChecked();
  });

  test('should check if invalid zygosity state is reset when switching tools', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const zygosity = genotypeBrowser.genotypeBlock.zygosity;
    await zygosity.checkbox('pedigreeSelector', 'homozygous').uncheck();
    await zygosity.checkbox('pedigreeSelector', 'heterozygous').uncheck();
    await expect(zygosity.selectAtLeastOneError('pedigreeSelector')).toBeVisible();

    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();

    await genotypeBrowser.openToolLink('Gene Browser');
    await genotypeBrowser.openToolLink('Genotype Browser');

    await expect(zygosity.checkbox('pedigreeSelector', 'homozygous')).toBeChecked();
    await expect(zygosity.checkbox('pedigreeSelector', 'heterozygous')).toBeChecked();
    await expect(zygosity.selectAtLeastOneError('pedigreeSelector')).not.toBeVisible();

    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
  });

  test('should check if zygosity is not visible in Phenotype Tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.openToolLink('Phenotype Tool');
    await expect(genotypeBrowser.genotypeBlock.zygosity.filter('presentInParent')).not.toBeVisible();
    await expect(genotypeBrowser.genotypeBlock.effectTypes.zygosityFilter).not.toBeVisible();
  });
});
