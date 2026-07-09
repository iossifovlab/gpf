import { Locator, Page } from '@playwright/test';

// Component object for the numeric (continuous) histogram: the from/to
// range inputs, their step up/down buttons and the sum-of-bars label.
// Page-scoped, matching the specs (ids are unique on the active widget).
export class NumberHistogram {
  public readonly root: Locator;
  public readonly fromInput: Locator;
  public readonly toInput: Locator;
  public readonly stepFromUp: Locator;
  public readonly stepFromDown: Locator;
  public readonly stepToUp: Locator;
  public readonly stepToDown: Locator;
  public readonly sumOfBarsLabel: Locator;

  // range validation messages
  public readonly rangeStartBelowMinError: Locator;
  public readonly rangeEndAboveMaxError: Locator;
  public readonly rangeStartAfterEndError: Locator;
  public readonly rangeEndBeforeStartError: Locator;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-histogram');
    this.fromInput = page.locator('input#from-input-field');
    this.toInput = page.locator('input#to-input-field');
    this.stepFromUp = page.locator('.histogram-from .step.up');
    this.stepFromDown = page.locator('.histogram-from .step.down');
    this.stepToUp = page.locator('.histogram-to .step.up');
    this.stepToDown = page.locator('.histogram-to .step.down');
    this.sumOfBarsLabel = page.locator('text#sumOfBarsLabel');

    this.rangeStartBelowMinError = page.getByText('Range start should be more than or equal to domain min.');
    this.rangeEndAboveMaxError = page.getByText('Range end should be less than or equal to domain max.');
    this.rangeStartAfterEndError = page.getByText('Range start should be less than or equal to range end.');
    this.rangeEndBeforeStartError = page.getByText('Range end should be more than or equal to range start.');
  }
}
