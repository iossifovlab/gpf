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
  setGenomicScoresCategorical,
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
  @Input() public otherGenomicScores: GenomicScore[];
  @Output() public changeGenomicScore = new EventEmitter<{ old: string, new: string }>();
  @Output() public updateState = new EventEmitter<GenomicScoreState>();
  public errors: string[] = [];

  // Refactor needed, not removal.
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store
  ) { }

  public ngOnInit(): void {
    this.localState = this.initialState;
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

  public updateSelectedGenomicScore(newGenomicScore: GenomicScore): void {
    this.changeGenomicScore.emit({
      old: this.selectedGenomicScore.score,
      new: newGenomicScore.score
    });
  }

  private updateHistogramState(): void {
    this.validateState(this.localState);
    this.updateState.emit(this.localState);
  }

  public switchCategoricalHistogramView(view: CategoricalHistogramView): void {
    if (view === this.localState.categoricalView) {
      return;
    }
    this.localState.categoricalView = view;
    this.localState.values = [];
    this.updateHistogramState();
  }

  public toggleCategoricalValues(values: string[]): void {
    const oldValues: Set<string> = new Set([...this.localState.values]);
    const newValues: Set<string> = new Set([...values]);

    this.localState.values = Array.from(oldValues.symmetricDifference(newValues));
    const cloned = cloneDeep(this.localState.values);
    this.validateState(this.localState);
    this.store.dispatch(setGenomicScoresCategorical({
      score: this.localState.score,
      values: cloned,
      categoricalView: this.localState.categoricalView,
    }));
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
        this.errors.push('Please select at least one bar.');
      }
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'genomicScores', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'genomicScores'}));
    }
  }
}
