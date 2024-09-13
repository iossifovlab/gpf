import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { reset } from 'app/users/state-actions';

export interface GeneScoresState {
  geneScore: string;
  rangeStart: number;
  rangeEnd: number;
}

export const initialState: GeneScoresState = {
  geneScore: null,
  rangeStart: 0,
  rangeEnd: 0
};

export const selectGeneScores =
  createFeatureSelector<GeneScoresState>('geneScores');

export const setGeneScoresHistogramValues = createAction(
  '[Genotype] Set geneScores histogram values',
  props<{ geneScore: string; rangeStart: number; rangeEnd: number }>()
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
  on(setGeneScoresHistogramValues, (state, { geneScore, rangeStart, rangeEnd }) => ({
    geneScore: geneScore,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd
  })),
  on(setGeneScore, (state, { geneScore, rangeStart, rangeEnd }) => ({
    geneScore: geneScore,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd
  })),
  on(reset, resetGeneScoresValues, state => cloneDeep(initialState))
);
