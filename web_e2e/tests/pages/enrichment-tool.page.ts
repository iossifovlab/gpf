import { Locator, Page } from '@playwright/test';
import { GenesBlock } from '../components/genes-block.component';

// Page object for the Enrichment tool, composing the genes block with the
// enrichment-specific models block, table and query controls.
export class EnrichmentToolPage {
  public readonly genesBlock: GenesBlock;

  public readonly modelsBlock: Locator;
  public readonly enrichmentTable: Locator;
  public readonly backgroundModels: Locator;
  public readonly countingModels: Locator;
  public readonly searchBox: Locator;

  public readonly enrichmentTestButton: Locator;
  public readonly shareSaveQueryButton: Locator;

  public readonly insertGeneSymbolError: Locator;
  public readonly selectGeneSetError: Locator;

  public constructor(private readonly page: Page) {
    this.genesBlock = new GenesBlock(page);

    this.modelsBlock = page.locator('gpf-enrichment-models-block');
    this.enrichmentTable = page.locator('.enrichment-table');
    this.backgroundModels = page.locator('#background-models');
    this.countingModels = page.locator('#counting-models');
    this.searchBox = page.locator('#search-box');

    this.enrichmentTestButton = page.getByRole('button', { name: 'Enrichment test' });
    this.shareSaveQueryButton = page.getByRole('button', { name: 'Share/save query' });

    this.insertGeneSymbolError = page.getByText('Please insert at least one gene symbol.');
    this.selectGeneSetError = page.getByText('Please select a gene set.');
  }

  // A cell in the enrichment result table by row and column index.
  public tableCell(row: number, column: number): Locator {
    return this.enrichmentTable.locator('tr').nth(row).locator('td').nth(column);
  }
}
