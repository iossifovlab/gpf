import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { reset } from 'app/users/state-actions';

export interface GeneScoresState {
  score: string;
  rangeStart: number;
  rangeEnd: number;
  values: string[];
}

export const initialState: GeneScoresState = {
  score: null,
  rangeStart: 0,
  rangeEnd: 0,
  values: null,
};

export const selectGeneScores =
  createFeatureSelector<GeneScoresState>('geneScores');

export const setGeneScoreContinuous = createAction(
  '[Genotype] Set score with continuous histogram data',
  props<{score: string, rangeStart: number, rangeEnd: number}>()
);

export const setGeneScoreCategorical = createAction(
  '[Genotype] Set score with categorical histogram data',

  props<{score: string, values: string[]}>()
);

export const resetGeneScoresValues = createAction(
  '[Genotype] Reset geneScores values'
);

export const geneScoresReducer = createReducer(
  initialState,
  on(setGeneScoreContinuous, (state, { score, rangeStart, rangeEnd }) => ({
    score: score,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd,
    values: initialState.values,
  })),
  on(setGeneScoreCategorical, (state, { score, values }) => ({
    score: score,
    rangeStart: initialState.rangeStart,
    rangeEnd: initialState.rangeEnd,
    values: values,
  })),
  on(reset, resetGeneScoresValues, state => cloneDeep(initialState))
);
