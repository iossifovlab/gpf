import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import {
  Partitions,
  GeneScoresLocalState,
} from './gene-scores';
import { GeneScoresService } from './gene-scores.service';
import { ReplaySubject, Observable, combineLatest, of } from 'rxjs';
import { Store } from '@ngrx/store';
import { ConfigService } from '../config/config.service';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap, take } from 'rxjs/operators';
import { ArrayNotEmpty, ValidateIf, ValidateNested } from 'class-validator';
import { environment } from 'environments/environment';
import { ComponentValidator } from 'app/common/component-validator';
import {
  selectGeneScores,
  setGeneScoreCategorical,
  setGeneScoreContinuous
} from './gene-scores.state';
import { cloneDeep } from 'lodash';
import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';
import { CategoricalHistogramView, CategoricalHistogram, NumberHistogram } from 'app/utils/histogram-types';

@Component({
  encapsulation: ViewEncapsulation.None, // TODO: What is this?
  selector: 'gpf-gene-scores',
  templateUrl: './gene-scores.component.html',
  styleUrls: ['./gene-scores.component.css'],
})
export class GeneScoresComponent extends ComponentValidator implements OnInit {
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);
  private partitions: Observable<Partitions>;

  public geneScoresArray: GenomicScore[];
  public rangesCounts: Observable<Array<number>>;
  public downloadUrl: string;

  @ValidateNested() public geneScoresLocalState = new GeneScoresLocalState();
  @ValidateIf(
    (component: GeneScoresComponent) => component.isCategoricalHistogram(component.selectedGeneScore.histogram)
  )
  @ArrayNotEmpty({message: 'Please select at least one value.'})
  public categoricalValues: string[] = [];
  public selectedCategoricalHistogramView: CategoricalHistogramView = 'range selector';

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store,
    private geneScoresService: GeneScoresService,
    private config: ConfigService
  ) {
    super(store, 'geneScores', selectGeneScores);
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
  }

  public ngOnInit(): void {
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
            break;
          }
        }
      } else {
        this.selectedGeneScore = this.geneScoresArray[0];
      }
      super.ngOnInit();
    });

    if (this.geneScoresLocalState.score !== null) {
      if (this.rangeStart !== 0 && this.rangeEnd !== 0) {
        this.updateContinuousHistogramState();
      }
      if (this.categoricalValues.length > 0) {
        this.updateCategoricalHistogramState();
      }
    }
  }

  private updateLabels(): void {
    this.rangeChanges.next([
      this.geneScoresLocalState.score?.score,
      this.rangeStart,
      this.rangeEnd
    ]);
  }

  private updateContinuousHistogramState(): void {
    this.updateLabels();
    this.store.dispatch(setGeneScoreContinuous({
      score: this.selectedGeneScore.score,
      rangeStart: this.geneScoresLocalState.rangeStart,
      rangeEnd: this.geneScoresLocalState.rangeEnd,
    }));
  }

  private updateCategoricalHistogramState(): void {
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
    return this.geneScoresLocalState.score;
  }

  public set selectedGeneScore(selectedGeneScore: GenomicScore) {
    this.categoricalValues = [];
    this.geneScoresLocalState.score = selectedGeneScore;
    this.downloadUrl = this.getDownloadUrl();
    if (selectedGeneScore !== undefined && this.isNumberHistogram(selectedGeneScore.histogram)) {
      this.changeDomain(selectedGeneScore.histogram);
      this.rangeStart = this.geneScoresLocalState.domainMin;
      this.rangeEnd = this.geneScoresLocalState.domainMax;
      this.updateLabels();
      this.store.dispatch(setGeneScoreContinuous({
        score: this.geneScoresLocalState.score.score,
        rangeStart: this.geneScoresLocalState.rangeStart,
        rangeEnd: this.geneScoresLocalState.rangeEnd,
      }));
    } else if (this.isCategoricalHistogram(selectedGeneScore.histogram)) {
      this.rangeStart = null;
      this.rangeEnd = null;
      if (!(this.selectedGeneScore.histogram as CategoricalHistogram).valueOrder) {
        this.selectedCategoricalHistogramView = 'click selector';
      }
    }
  }

  public set rangeStart(range: number) {
    this.geneScoresLocalState.rangeStart = range;
    this.updateContinuousHistogramState();
  }

  public get rangeStart(): number {
    return this.geneScoresLocalState.rangeStart;
  }

  public set rangeEnd(range: number) {
    this.geneScoresLocalState.rangeEnd = range;
    this.updateContinuousHistogramState();
  }

  public get rangeEnd(): number {
    return this.geneScoresLocalState.rangeEnd;
  }

  private getDownloadUrl(): string {
    if (this.selectedGeneScore !== undefined) {
      return `${this.config.baseUrl}gene_scores/download/${this.selectedGeneScore.score}`;
    }
  }

  private changeDomain(histogram: NumberHistogram): void {
    if (histogram.rangeMin && histogram.rangeMax) {
      this.geneScoresLocalState.domainMin = histogram.rangeMin;
      this.geneScoresLocalState.domainMax = histogram.rangeMax;
    } else {
      this.geneScoresLocalState.domainMin = histogram.bins[0];
      this.geneScoresLocalState.domainMax = histogram.bins[histogram.bins.length - 1];
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
    this.store.dispatch(setGeneScoreCategorical({
      score: this.geneScoresLocalState.score.score,
      values: cloneDeep(this.categoricalValues),
      categoricalView: this.selectedCategoricalHistogramView,
    }));
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }
}
