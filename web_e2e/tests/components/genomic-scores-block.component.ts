import { Locator, Page } from '@playwright/test';

// Component object for the `gpf-genomic-scores-block` widget: the score
// selector dropdown plus the list of added `gpf-genomic-scores` histograms
// (continuous with from/to inputs, or categorical with a values dropdown).
// Most locators are page-scoped and addressed by index since several
// scores can be added at once, matching the specs.
export class GenomicScoresBlock {
  public readonly root: Locator;
  public readonly scoreSelector: Locator;
  public readonly helpIcon: Locator;
  public readonly matOptions: Locator;
  public readonly scores: Locator;
  public readonly scoreTitles: Locator;
  public readonly removeButton: Locator;
  public readonly categoricalRemoveButton: Locator;
  public readonly helperModal: Locator;
  public readonly categoricalValuesDropdown: Locator;
  public readonly errorsAlert: Locator;
  public readonly searchBox: Locator;
  public readonly categoricalSearchBox: Locator;
  public readonly valueWrapper: Locator;
  public readonly valuesList: Locator;
  public readonly valuesSuggestionsDropdown: Locator;
  public readonly fromInputs: Locator;
  public readonly toInputs: Locator;
  public readonly partitionsText: Locator;
  public readonly descriptionModal: Locator;
  public readonly closeButton: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-genomic-scores-block');
    this.scoreSelector = this.root.locator('mat-form-field');
    this.helpIcon = this.root.locator('#help-icon');
    this.matOptions = page.locator('mat-option');
    this.scores = page.locator('gpf-genomic-scores');
    this.scoreTitles = page.locator('gpf-genomic-scores .title-wrapper');
    this.removeButton = page.locator('#remove-button');
    this.categoricalRemoveButton = page.locator('gpf-remove-button');
    this.helperModal = page.locator('gpf-helper-modal');
    this.categoricalValuesDropdown = page.locator('gpf-categorical-values-dropdown');
    this.errorsAlert = page.locator('gpf-genomic-scores gpf-errors-alert');
    this.searchBox = page.locator('#search-box');
    this.categoricalSearchBox = page.locator('gpf-categorical-values-dropdown #search-box');
    this.valueWrapper = page.locator('.value-wrapper');
    this.valuesList = page.locator('#values-list');
    this.valuesSuggestionsDropdown = page.locator('.values-suggestions-dropdown');
    this.fromInputs = page.locator('input#from-input-field');
    this.toInputs = page.locator('input#to-input-field');
    this.partitionsText = page.locator('text.partitions-text');
    this.descriptionModal = page.locator('.modal-content');
    this.closeButton = this.descriptionModal.locator('#close-button');
  }

  // The score dropdown option (clickable `span` inside the mat-option).
  public scoreOption(text: string): Locator {
    return this.page.locator(`mat-option:has-text("${text}") span`);
  }

  // The score dropdown option row (used for visibility assertions).
  public scoreOptionRow(text: string): Locator {
    return this.page.locator(`mat-option:has-text("${text}")`);
  }

  // A categorical value option matched by regex on its label.
  public valueOption(pattern: RegExp): Locator {
    return this.page.locator('mat-option > span > span').filter({ hasText: pattern });
  }

  // A categorical value option matched by exact label text.
  public valueOptionByText(text: string): Locator {
    return this.page.locator(`mat-option:has-text("${text}") > span > span`);
  }

  public score(index: number): Locator {
    return this.scores.nth(index);
  }

  public scoreSearchBox(index: number): Locator {
    return this.scores.nth(index).locator('#search-box');
  }

  public errorsAlertContaining(text: string): Locator {
    return this.page.locator('gpf-errors-alert').filter({ hasText: text });
  }

  public async openScoreDropdown(): Promise<void> {
    await this.scoreSelector.click();
  }

  public async selectScore(text: string): Promise<void> {
    await this.scoreSelector.click();
    await this.scoreOption(text).click();
  }
}
