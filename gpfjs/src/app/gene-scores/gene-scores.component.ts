import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { GeneScoresLocalState, GeneScores, CategoricalHistogram, NumberHistogram } from './gene-scores';
import { GeneScoresService } from './gene-scores.service';
import { ReplaySubject, combineLatest, of } from 'rxjs';
import { Store } from '@ngrx/store';
import { ConfigService } from '../config/config.service';
import { switchMap, take } from 'rxjs/operators';
import { ValidateNested } from 'class-validator';
import { environment } from 'environments/environment';
import { ComponentValidator } from 'app/common/component-validator';
import { selectGeneScores, setGeneScoreCategorical, setGeneScoreContinuous } from './gene-scores.state';
import { cloneDeep } from 'lodash';

@Component({
  encapsulation: ViewEncapsulation.None, // TODO: What is this?
  selector: 'gpf-gene-scores',
  templateUrl: './gene-scores.component.html',
  styleUrls: ['./gene-scores.component.css'],
})
export class GeneScoresComponent extends ComponentValidator implements OnInit {
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public geneScoresArray: GeneScores[];
  public downloadUrl: string;

  @ValidateNested() public geneScoresLocalState = new GeneScoresLocalState();
  public categoricalValues: string[] = [];

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store,
    private geneScoresService: GeneScoresService,
    private config: ConfigService
  ) {
    super(store, 'geneScores', selectGeneScores);
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
            this.selectedGeneScores = score;
            // Load either categorical or continuous histogram selection data
            if (state.values?.length > 0) {
              this.categoricalValues = cloneDeep(state.values);
            } else {
              this.rangeStart = state.rangeStart;
              this.rangeEnd = state.rangeEnd;
            }
            break;
          }
        }
      } else {
        this.selectedGeneScores = this.geneScoresArray[0];
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
      score: this.selectedGeneScores.score,
      rangeStart: this.geneScoresLocalState.rangeStart,
      rangeEnd: this.geneScoresLocalState.rangeEnd,
    }));
  }

  private updateCategoricalHistogramState(): void {
    this.store.dispatch(setGeneScoreCategorical({
      score: this.selectedGeneScores.score,
      values: this.categoricalValues,
    }));
  }

  public get selectedGeneScores(): GeneScores {
    return this.geneScoresLocalState.score;
  }

  public set selectedGeneScores(selectedGeneScores: GeneScores) {
    this.geneScoresLocalState.score = selectedGeneScores;
    this.downloadUrl = this.getDownloadUrl();
    if (selectedGeneScores !== undefined && this.isNumberHistogram(selectedGeneScores.histogram)) {
      this.changeDomain(selectedGeneScores.histogram);
      this.rangeStart = this.geneScoresLocalState.domainMin;
      this.rangeEnd = this.geneScoresLocalState.domainMax;
      this.updateLabels();
      this.store.dispatch(setGeneScoreContinuous({
        score: this.geneScoresLocalState.score.score,
        rangeStart: this.geneScoresLocalState.rangeStart,
        rangeEnd: this.geneScoresLocalState.rangeEnd,
      }));
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
    if (this.selectedGeneScores !== undefined) {
      return `${this.config.baseUrl}gene_scores/download/${this.selectedGeneScores.score}`;
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
    }));
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }
}
