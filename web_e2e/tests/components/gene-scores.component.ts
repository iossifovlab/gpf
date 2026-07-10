import { Locator, Page } from '@playwright/test';
import { NumberHistogram } from './number-histogram.component';
import { CategoricalHistogram } from './categorical-histogram.component';

// Component object for the `gpf-gene-scores` widget: the score-select
// dropdown, the download link and the two histogram types the widget can
// render depending on the selected score.
export class GeneScores {
  public readonly root: Locator;
  public readonly select: Locator;
  public readonly downloadLink: Locator;
  public readonly errorsAlert: Locator;
  public readonly numberHistogram: NumberHistogram;
  public readonly categorical: CategoricalHistogram;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-gene-scores');
    this.select = this.root.locator('select');
    this.downloadLink = this.root.locator('.download-link');
    this.errorsAlert = this.root.locator('gpf-errors-alert');
    this.numberHistogram = new NumberHistogram(page);
    this.categorical = new CategoricalHistogram(page);
  }

  public async selectScore(label: string): Promise<void> {
    await this.select.selectOption(label);
  }
}
