import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = [];

export const selectGenomicScores = createFeatureSelector<object[]>('genomicScores');

export const setGenomicScores = createAction(
  '[Genotype] Set genomic scores',
  props<{ genomicScores: object[] }>()
);

export const resetGenomicScores = createAction(
  '[Genotype] Reset genomic scores'
);

export const genomicScoresReducer = createReducer(
  initialState,
  on(setGenomicScores, (state, {genomicScores}) => genomicScores),
  on(resetGenomicScores, state => []),
);
