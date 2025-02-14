import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { environment } from 'environments/environment';
import { ReplaySubject} from 'rxjs';
import {
  CategoricalHistogram,
  CategoricalHistogramView,
  GenomicScore,
  NumberHistogram
} from '../genomic-scores-block/genomic-scores-block';
import { cloneDeep } from 'lodash';
import { Store } from '@ngrx/store';
import {
  GenomicScoreState,
} from 'app/genomic-scores-block/genomic-scores-block.state';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
  styleUrls: ['./genomic-scores.component.css']
})
export class GenomicScoresComponent implements OnInit {
  @Input() public selectedGenomicScore: GenomicScore;
  @Input() public initialState: GenomicScoreState;
  public localState: GenomicScoreState;
  @Output() public updateState = new EventEmitter<GenomicScoreState>();
  public errors: string[] = [];
  private categoricalValueMax = 1000;
  private readonly maxBarCount = 25;

  // Refactor needed, not removal.
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store
  ) { }

  public ngOnInit(): void {
    this.localState = cloneDeep(this.initialState);
    this.validateState(this.localState);

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
    this.validateState(this.localState);
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

  public toggleCategoricalValues(values: string[]): void {
    const oldValues: Set<string> = new Set(this.localState.values);
    const newValues: Set<string> = new Set(values);

    this.localState.values = Array.from(oldValues.symmetricDifference(newValues));
    this.updateHistogramState();
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }

  private validateState(state: GenomicScoreState): void {
    this.errors = [];
    if (!state.score) {
      this.errors.push('Empty score names are invalid.');
    }
    if (this.isNumberHistogram(this.selectedGenomicScore.histogram)) {
      if (state.rangeStart !== null) {
        if (typeof state.rangeStart !== 'number') {
          this.errors.push('Range start should be a number.');
        }
        if (state.rangeStart > state.rangeEnd) {
          this.errors.push('Range start should be less than or equal to range end.');
        }
        if (state.rangeStart < this.selectedGenomicScore.histogram.rangeMin) {
          this.errors.push('Range start should be more than or equal to domain min.');
        }
      }
      if (state.rangeEnd !== null) {
        if (typeof state.rangeEnd !== 'number') {
          this.errors.push('Range end should be a number.');
        }
        if (state.rangeEnd < state.rangeStart) {
          this.errors.push('Range end should be more than or equal to range start.');
        }
        if (state.rangeEnd > this.selectedGenomicScore.histogram.rangeMax) {
          this.errors.push('Range end should be less than or equal to domain max.');
        }
      }
    }
    if (this.isCategoricalHistogram(this.selectedGenomicScore.histogram)) {
      if (!state.values.length) {
        this.errors.push('Please select at least one value.');
      }
      if (state.values.length > this.categoricalValueMax) {
        this.errors.push(`Please select less than ${this.categoricalValueMax} values.`);
      }
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
