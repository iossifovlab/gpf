import { Component, OnInit } from '@angular/core';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { Store} from '@ngrx/store';
import {
  GenomicScoreState,
  removeGenomicScore,
  selectGenomicScores,
  setGenomicScoresCategorical,
  setGenomicScoresContinuous
} from './genomic-scores-block.state';
import { combineLatest, of } from 'rxjs';
import { switchMap, take } from 'rxjs/operators';
import { cloneDeep } from 'lodash';
import { resetErrors } from 'app/common/errors.state';
import { CategoricalHistogram } from 'app/utils/histogram-types';
import { GenomicScore } from './genomic-scores-block';

@Component({
    selector: 'gpf-genomic-scores-block',
    templateUrl: './genomic-scores-block.component.html',
    styleUrls: ['./genomic-scores-block.component.css'],
    standalone: false
})
export class GenomicScoresBlockComponent implements OnInit {
  public selectedGenomicScores: {score: GenomicScore, state: GenomicScoreState}[] = [];
  public unusedGenomicScores: GenomicScore[];
  public allGenomicScores: GenomicScore[];

  public constructor(
    protected store: Store,
    private genomicScoresBlockService: GenomicScoresBlockService,
  ) { }

  public ngOnInit(): void {
    this.genomicScoresBlockService.getGenomicScores().pipe(
      take(1),
      switchMap(genomicScores => combineLatest([
        of(genomicScores),
        this.store.select(selectGenomicScores)
      ]))
    ).pipe(take(1)).subscribe(([genomicScores, genomicScoresState]) => {
      this.allGenomicScores = genomicScores;
      if (genomicScoresState.length > 0) {
        // restore state
        for (const state of genomicScoresState) {
          this.selectedGenomicScores.unshift({
            score: genomicScores.find(score => score.score === state.score),
            state: state,
          });
        }
        // set visible scores after restore
        this.unusedGenomicScores = this.allGenomicScores
          .filter(gs => !this.selectedGenomicScores.find(selected => selected.state.score === gs.score));
      } else {
        this.unusedGenomicScores = [...this.allGenomicScores];
      }
      this.unusedGenomicScores.sort((a, b) => a.score.localeCompare(b.score));
    });
  }

  private createScoreDefaultState(score: GenomicScore): GenomicScoreState {
    const state: GenomicScoreState = {
      histogramType: null,
      score: null,
      rangeStart: null,
      rangeEnd: null,
      values: null,
      categoricalView: null,
    };
    state.score = score.score;
    if (score.histogram instanceof CategoricalHistogram) {
      state.histogramType = 'categorical';
      state.rangeStart = null;
      state.rangeEnd = null;
      state.values = score.histogram.values.map(value => value.name);
      state.categoricalView = 'range selector';
    } else {
      state.histogramType = 'continuous';
      state.rangeStart = score.histogram.rangeMin;
      state.rangeEnd = score.histogram.rangeMax;
      state.values = null;
      state.categoricalView = null;
    }
    return state;
  }

  public addFilter(score: GenomicScore, index: number): void {
    const defaultState = this.createScoreDefaultState(score);
    this.selectedGenomicScores.unshift({
      score: score,
      state: defaultState,
    });
    this.unusedGenomicScores.splice(index, 1);
    this.addToState(cloneDeep(defaultState));
  }

  public removeFromState(state: GenomicScoreState): void {
    const oldIndex = this.selectedGenomicScores.findIndex(selected => selected.score.score === state.score);
    this.unusedGenomicScores.push(this.selectedGenomicScores[oldIndex].score);
    this.unusedGenomicScores.sort((a, b) => a.score.localeCompare(b.score));
    this.selectedGenomicScores.splice(oldIndex, 1);
    this.store.dispatch(removeGenomicScore({genomicScoreName: state.score}));
    this.store.dispatch(resetErrors({componentId: `genomicScores: ${state.score}`}));
  }

  public addToState(state: GenomicScoreState): void {
    state = cloneDeep(state);
    if (state.histogramType === 'continuous') {
      this.store.dispatch(setGenomicScoresContinuous({
        score: state.score,
        rangeStart: state.rangeStart,
        rangeEnd: state.rangeEnd,
      }));
    } else if (state.histogramType === 'categorical') {
      this.store.dispatch(setGenomicScoresCategorical({
        score: state.score,
        values: state.values,
        categoricalView: state.categoricalView,
      }));
    }
  }
}
