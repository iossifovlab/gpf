import { Locator, Page } from '@playwright/test';
import { GeneSymbols } from './gene-symbols.component';
import { GeneSets } from './gene-sets.component';
import { GeneScores } from './gene-scores.component';

// Component object for the `gpf-genes-block` widget: the Gene Symbols /
// Gene Sets / Gene Scores tabs plus the nested sub-components.
export class GenesBlock {
  public readonly root: Locator;
  public readonly geneSymbols: GeneSymbols;
  public readonly geneSets: GeneSets;
  public readonly geneScores: GeneScores;

  // panel + toggle locators
  public readonly geneSymbolsToggle: Locator;
  public readonly geneSetsToggle: Locator;
  public readonly geneScoresToggle: Locator;
  public readonly geneSymbolsPanel: Locator;
  public readonly geneSetsPanel: Locator;
  public readonly geneSetsPanelWrapper: Locator;
  public readonly geneScoresPanel: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-genes-block');
    this.geneSymbols = new GeneSymbols(page);
    this.geneSets = new GeneSets(page);
    this.geneScores = new GeneScores(page);

    this.geneSymbolsToggle = page.locator('#gene-symbols');
    this.geneSetsToggle = page.locator('#gene-sets');
    this.geneScoresToggle = page.locator('#gene-scores');
    this.geneSymbolsPanel = page.locator('#gene-symbols-panel');
    this.geneSetsPanel = page.locator('#gene-sets-panel');
    this.geneSetsPanelWrapper = page.locator('.gene-sets-panel');
    this.geneScoresPanel = page.locator('#gene-scores-panel');
  }

  public async openGeneSymbols(): Promise<void> {
    await this.geneSymbolsToggle.click();
  }

  public async openGeneSets(): Promise<void> {
    await this.geneSetsToggle.click();
  }

  public async openGeneScores(): Promise<void> {
    await this.geneScoresToggle.click();
  }

  public async openGeneSymbolsTab(): Promise<void> {
    await this.page.getByRole('tab', { name: 'Gene Symbols' }).click();
  }

  public async openGeneSetsTab(): Promise<void> {
    await this.page.getByRole('tab', { name: 'Gene Sets' }).click();
  }

  public async openGeneScoresTab(): Promise<void> {
    await this.page.getByRole('tab', { name: 'Gene Scores' }).click();
  }

  public async openAllTab(): Promise<void> {
    await this.root.getByRole('tab', { name: 'All' }).click();
  }
}
