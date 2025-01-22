import { Component, OnInit } from '@angular/core';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { CategoricalHistogram, GenomicScore } from './genomic-scores-block';
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

@Component({
  selector: 'gpf-genomic-scores-block',
  templateUrl: './genomic-scores-block.component.html',
  styleUrls: ['./genomic-scores-block.component.css'],
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
          this.selectedGenomicScores.push({
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

  public addFilter(): void {
    const defaultState = this.createScoreDefaultState(this.unusedGenomicScores[0]);
    this.selectedGenomicScores.push({
      score: this.unusedGenomicScores[0],
      state: defaultState,
    });
    this.unusedGenomicScores.splice(0, 1);
    this.addToState(cloneDeep(defaultState));
  }

  public changeFilter(change: {old: string, new: string}): void {
    // Add the old genomic score to the unused list
    const oldIndex = this.selectedGenomicScores.findIndex(selected => selected.score.score === change.old);
    this.unusedGenomicScores.push(this.selectedGenomicScores[oldIndex].score);
    this.unusedGenomicScores.sort((a, b) => a.score.localeCompare(b.score));

    // Add the unused genomic score to the selected and update the state
    this.store.dispatch(removeGenomicScore({genomicScoreName: this.selectedGenomicScores[oldIndex].state.score}));
    const newIndex = this.unusedGenomicScores.findIndex(unused => unused.score === change.new);
    const defaultState = this.createScoreDefaultState(this.unusedGenomicScores[newIndex]);
    this.selectedGenomicScores[oldIndex] = {
      score: this.unusedGenomicScores[newIndex],
      state: defaultState,
    };
    this.addToState(cloneDeep(defaultState));
    this.unusedGenomicScores.splice(newIndex, 1);
  }

  public removeFromState(state: GenomicScoreState): void {
    const oldIndex = this.selectedGenomicScores.findIndex(selected => selected.score.score === state.score);
    this.unusedGenomicScores.push(this.selectedGenomicScores[oldIndex].score);
    this.unusedGenomicScores.sort((a, b) => a.score.localeCompare(b.score));
    this.selectedGenomicScores.splice(oldIndex, 1);
    this.store.dispatch(removeGenomicScore({genomicScoreName: state.score}));
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
