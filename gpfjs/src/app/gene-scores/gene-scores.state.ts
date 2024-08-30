import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { GeneScores } from './gene-scores';

export interface GeneScoresState {
  geneScores: GeneScores;
  rangeStart: number;
  rangeEnd: number;
}

export const initialState: GeneScoresState = {
  geneScores: null,
  rangeStart: 0,
  rangeEnd: 0
};

export const selectGeneScores =
  createFeatureSelector<GeneScoresState>('geneScores');

export const setGeneScoresHistogramValues = createAction(
  '[Genotype] Set geneScores histogram values',
  props<{ rangeStart: number; rangeEnd: number }>()
);

export const setGeneScore = createAction(
  '[Genotype] Set geneScore',
  props<GeneScoresState>()
);

export const resetGeneScoresValues = createAction(
  '[Genotype] Reset geneScores values'
);

export const geneScoresReducer = createReducer(
  initialState,
  on(setGeneScoresHistogramValues, (state, { rangeStart, rangeEnd }) => ({
    ...state,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd
  })),
  on(setGeneScore, (state, { geneScores, rangeStart, rangeEnd }) => ({
    geneScores: cloneDeep(geneScores),
    rangeStart: rangeStart,
    rangeEnd: rangeEnd
  })),
  on(resetGeneScoresValues, state => cloneDeep(initialState))
);
