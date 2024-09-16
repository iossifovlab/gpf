import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { reset } from 'app/users/state-actions';

export interface GeneScoresState {
  score: string;
  rangeStart: number;
  rangeEnd: number;
}

export const initialState: GeneScoresState = {
  score: null,
  rangeStart: 0,
  rangeEnd: 0
};

export const selectGeneScores =
  createFeatureSelector<GeneScoresState>('geneScores');

export const setGeneScoresHistogramValues = createAction(
  '[Genotype] Set geneScores histogram values',
  props<{ score: string; rangeStart: number; rangeEnd: number }>()
);

export const setGeneScore = createAction(
  '[Genotype] Set score',
  props<GeneScoresState>()
);

export const resetGeneScoresValues = createAction(
  '[Genotype] Reset geneScores values'
);

export const geneScoresReducer = createReducer(
  initialState,
  on(setGeneScoresHistogramValues, (state, { score, rangeStart, rangeEnd }) => ({
    score: score,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd
  })),
  on(setGeneScore, (state, { score, rangeStart, rangeEnd }) => ({
    score: score,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd
  })),
  on(reset, resetGeneScoresValues, state => cloneDeep(initialState))
);
