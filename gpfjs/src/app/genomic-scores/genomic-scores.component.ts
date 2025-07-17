import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { environment } from 'environments/environment';
import { ReplaySubject} from 'rxjs';

import { cloneDeep } from 'lodash';
import { Store } from '@ngrx/store';
import {
  GenomicScoreState,
} from 'app/genomic-scores-block/genomic-scores-block.state';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';
import { NumberHistogram, CategoricalHistogramView, CategoricalHistogram } from 'app/utils/histogram-types';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
  styleUrls: ['./genomic-scores.component.css'],
  standalone: false
})
export class GenomicScoresComponent implements OnInit {
  @Input() public selectedGenomicScore: GenomicScore;
  @Input() public initialState: GenomicScoreState;
  public localState: GenomicScoreState;
  @Output() public updateState = new EventEmitter<GenomicScoreState>();
  public errors: string[] = [];
  public histogramErrors: string[] = [];
  private readonly maxBarCount = 25;

  // Refactor needed, not removal.
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store
  ) { }

  public ngOnInit(): void {
    this.localState = cloneDeep(this.initialState);
    this.validateState();

    const histogram = this.selectedGenomicScore.histogram;
    if (this.isCategoricalHistogram(histogram)) {
      let barCount = 0;
      if (histogram.displayedValuesCount) {
        barCount = histogram.displayedValuesCount;
      } else if (histogram.displayedValuesPercent) {
        barCount = Math.floor(histogram.values.length / 100 * histogram.displayedValuesPercent);
      }
      if (barCount > this.maxBarCount) {
        this.switchCategoricalHistogramView('dropdown selector');
      }
    }
  }

  public updateRangeStart(range): void {
    this.localState.rangeStart = range as number;
    this.updateHistogramState();
  }

  public updateRangeEnd(range): void {
    this.localState.rangeEnd = range as number;
    this.updateHistogramState();
  }

  public get domainMin(): number {
    return (this.selectedGenomicScore.histogram as NumberHistogram).bins[0];
  }

  public get domainMax(): number {
    const lastIndex = (this.selectedGenomicScore.histogram as NumberHistogram).bins.length - 1;
    return (this.selectedGenomicScore.histogram as NumberHistogram).bins[lastIndex];
  }

  public replaceCategoricalValues(values: string[]): void {
    this.localState.values = values;
    this.updateHistogramState();
  }

  private updateHistogramState(): void {
    this.validateState();
    this.updateState.emit(this.localState);
  }

  public switchCategoricalHistogramView(view: CategoricalHistogramView): void {
    if (view === this.localState.categoricalView) {
      return;
    }
    if (view === 'click selector' || view === 'dropdown selector') {
      this.localState.values = [];
    } else if (view === 'range selector' && this.isCategoricalHistogram(this.selectedGenomicScore.histogram)) {
      this.localState.values = this.selectedGenomicScore.histogram.values.map(v => v.name);
    }
    this.localState.categoricalView = view;
    this.updateHistogramState();
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }

  public setHistogramValidationErrors(errors: string[]): void {
    this.histogramErrors = errors;
    this.validateState();
  }

  private validateState(): void {
    this.errors = [];
    if (this.histogramErrors.length) {
      this.errors.push(...this.histogramErrors);
    }

    if (!this.localState.score) {
      this.errors.push('Empty score names are invalid.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: `genomicScores: ${this.selectedGenomicScore.score}`, errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: `genomicScores: ${this.selectedGenomicScore.score}`}));
    }
  }
}
