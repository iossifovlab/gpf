import { Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { Partitions } from './gene-scores';
import { GeneScoresService } from './gene-scores.service';
import { ReplaySubject, Observable, combineLatest, of } from 'rxjs';
import { Store } from '@ngrx/store';
import { ConfigService } from '../config/config.service';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap, take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import {
  selectGeneScores,
  setGeneScoreCategorical,
  setGeneScoreContinuous
} from './gene-scores.state';
import { cloneDeep } from 'lodash';
import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';
import { CategoricalHistogramView, CategoricalHistogram, NumberHistogram } from 'app/utils/histogram-types';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
  encapsulation: ViewEncapsulation.None, // TODO: What is this?
  selector: 'gpf-gene-scores',
  templateUrl: './gene-scores.component.html',
  styleUrls: ['./gene-scores.component.css'],
})
export class GeneScoresComponent implements OnInit, OnDestroy {
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);
  private partitions: Observable<Partitions>;

  public geneScoresArray: GenomicScore[];
  public rangesCounts: Observable<Array<number>>;
  public downloadUrl: string;

  public score: GenomicScore = null;
  public rangeStart: number = 0;
  public rangeEnd: number = 0;

  public domainMin = 0;
  public domainMax = 0;

  public categoricalValues: string[] = [];
  public selectedCategoricalHistogramView: CategoricalHistogramView = 'range selector';
  private categoricalValueMax = 1000;
  public errors: string[] = [];

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store,
    private geneScoresService: GeneScoresService,
    private config: ConfigService
  ) {}

  public ngOnInit(): void {
    this.partitions = this.rangeChanges.pipe(
      debounceTime(100),
      distinctUntilChanged(),
      switchMap(([score, internalRangeStart, internalRangeEnd]) =>
        this.geneScoresService.getPartitions(score, internalRangeStart, internalRangeEnd)
      ),
      catchError(error => {
        console.warn(error);
        return of(null);
      })
    );

    this.rangesCounts = this.partitions.pipe(
      map((partitions) =>
        [partitions.leftCount, partitions.midCount, partitions.rightCount]
      )
    );

    this.geneScoresService.getGeneScores().pipe(
      switchMap(geneScores =>
        combineLatest([of(geneScores), this.store.select(selectGeneScores).pipe(take(1))])
      )
    ).subscribe(([geneScores, state]) => {
      this.geneScoresArray = geneScores;

      if (state.score !== null) {
        for (const score of this.geneScoresArray) {
          if (score.score === state.score) {
            this.selectedGeneScore = score;
            // Load either categorical or continuous histogram selection data
            if (state.histogramType === 'categorical') {
              this.categoricalValues = cloneDeep(state.values);
              this.selectedCategoricalHistogramView = state.categoricalView;
            } else if (state.histogramType === 'continuous') {
              this.rangeStart = state.rangeStart;
              this.rangeEnd = state.rangeEnd;
            }
            this.validateState();
            break;
          }
        }
      } else {
        this.selectedGeneScore = this.geneScoresArray[0];
      }
    });

    if (this.score !== null) {
      if (this.rangeStart !== 0 && this.rangeEnd !== 0) {
        this.updateContinuousHistogramState();
      }
      if (this.categoricalValues.length > 0) {
        this.updateCategoricalHistogramState();
      }
    }
  }

  public ngOnDestroy(): void {
    this.store.dispatch(resetErrors({componentId: 'geneScores'}));
  }

  private updateLabels(): void {
    this.rangeChanges.next([
      this.score?.score,
      this.rangeStart,
      this.rangeEnd
    ]);
  }

  private updateContinuousHistogramState(): void {
    this.validateState();
    this.updateLabels();
    this.store.dispatch(setGeneScoreContinuous({
      score: this.selectedGeneScore.score,
      rangeStart: this.rangeStart,
      rangeEnd: this.rangeEnd,
    }));
  }

  private updateCategoricalHistogramState(): void {
    this.validateState();
    this.store.dispatch(setGeneScoreCategorical({
      score: this.selectedGeneScore.score,
      values: cloneDeep(this.categoricalValues),
      categoricalView: this.selectedCategoricalHistogramView,
    }));
  }

  public switchCategoricalHistogramView(view: CategoricalHistogramView): void {
    if (view === this.selectedCategoricalHistogramView) {
      return;
    }
    this.selectedCategoricalHistogramView = view;
    this.categoricalValues = [];
    this.updateCategoricalHistogramState();
  }

  public get selectedGeneScore(): GenomicScore {
    return this.score;
  }

  public set selectedGeneScore(selectedGeneScore: GenomicScore) {
    this.categoricalValues = [];
    this.score = selectedGeneScore;
    this.downloadUrl = this.getDownloadUrl();
    if (selectedGeneScore !== undefined && this.isNumberHistogram(selectedGeneScore.histogram)) {
      this.changeDomain(selectedGeneScore.histogram);
      this.rangeStart = this.domainMin;
      this.rangeEnd = this.domainMax;
      this.updateLabels();
      this.validateState();
      this.store.dispatch(setGeneScoreContinuous({
        score: this.score.score,
        rangeStart: this.rangeStart,
        rangeEnd: this.rangeEnd,
      }));
    } else if (this.isCategoricalHistogram(selectedGeneScore.histogram)) {
      this.rangeStart = null;
      this.rangeEnd = null;
      if (!(this.selectedGeneScore.histogram as CategoricalHistogram).valueOrder) {
        this.selectedCategoricalHistogramView = 'click selector';
      }
      this.validateState();
    }
  }

  public setRangeStart(range: number): void {
    if (this.isNumberHistogram(this.score.histogram)) {
      this.rangeStart = range;
      this.updateContinuousHistogramState();
    }
  }

  public setRangeEnd(range: number): void {
    if (this.isNumberHistogram(this.score.histogram)) {
      this.rangeEnd = range;
      this.updateContinuousHistogramState();
    }
  }

  private getDownloadUrl(): string {
    if (this.selectedGeneScore !== undefined) {
      return `${this.config.baseUrl}gene_scores/download/${this.selectedGeneScore.score}`;
    }
  }

  private changeDomain(histogram: NumberHistogram): void {
    if (histogram.rangeMin && histogram.rangeMax) {
      this.domainMin = histogram.rangeMin;
      this.domainMax = histogram.rangeMax;
    } else {
      this.domainMin = histogram.bins[0];
      this.domainMax = histogram.bins[histogram.bins.length - 1];
    }
  }

  public replaceCategoricalValues(values: string[]): void {
    this.categoricalValues = values;
    this.updateCategoricalHistogramState();
  }

  public toggleCategoricalValues(values: string[]): void {
    values.forEach(value => {
      const valueIndex = this.categoricalValues.findIndex(v => v === value);
      if (valueIndex === -1) {
        this.categoricalValues.push(value);
      } else {
        this.categoricalValues.splice(valueIndex, 1);
      }
    });
    this.updateCategoricalHistogramState();
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }

  private validateState(): void {
    this.errors = [];

    if (!this.score.score) {
      this.errors.push('Empty gene scores are invalid.');
    }
    if (this.isNumberHistogram(this.score.histogram)) {
      if (this.rangeStart !== null) {
        if (typeof this.rangeStart !== 'number') {
          this.errors.push('Range start should be a number.');
        }
        if (this.rangeStart > this.rangeEnd) {
          this.errors.push('Range start should be less than or equal to range end.');
        }
        if (this.rangeStart < this.score.histogram.rangeMin) {
          this.errors.push('Range start should be more than or equal to domain min.');
        }
      }
      if (this.rangeEnd !== null) {
        if (typeof this.rangeEnd !== 'number') {
          this.errors.push('Range end should be a number.');
        }
        if (this.rangeEnd < this.rangeStart) {
          this.errors.push('Range end should be more than or equal to range start.');
        }
        if (this.rangeEnd > this.score.histogram.rangeMax) {
          this.errors.push('Range end should be less than or equal to domain max.');
        }
      }
    }
    if (this.isCategoricalHistogram(this.score.histogram)) {
      if (!this.categoricalValues.length) {
        this.errors.push('Please select at least one value.');
      }
      if (this.categoricalValues.length > this.categoricalValueMax) {
        this.errors.push(`Please select less than ${this.categoricalValueMax} values.`);
      }
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'geneScores', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'geneScores'}));
    }
  }
}
