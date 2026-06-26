import { Component, EventEmitter, Input, OnInit, Output, inject } from '@angular/core';
import { environment } from 'environments/environment';
import { ReplaySubject} from 'rxjs';

import { cloneDeep } from 'lodash';
import { Store } from '@ngrx/store';
import {
  GenomicScoreState,
} from 'app/genomic-scores-block/genomic-scores-block.state';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';
import { NumberHistogram, CategoricalHistogram } from 'app/utils/histogram-types';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
  styleUrls: ['./genomic-scores.component.css'],
  standalone: false
})
export class GenomicScoresComponent implements OnInit {
  protected store = inject(Store);

  @Input() public selectedGenomicScore: GenomicScore;
  @Input() public initialState: GenomicScoreState;
  public localState: GenomicScoreState;
  @Output() public updateState = new EventEmitter<GenomicScoreState>();
  public errors: string[] = [];
  public histogramErrors: string[] = [];

  // Refactor needed, not removal.
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  public ngOnInit(): void {
    this.localState = cloneDeep(this.initialState);
    this.validateState();

    if (this.isCategoricalHistogram(this.selectedGenomicScore.histogram)
        && this.localState.categoricalView !== 'dropdown selector') {
      this.localState.values = [];
      this.localState.categoricalView = 'dropdown selector';
      this.updateHistogramState();
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
