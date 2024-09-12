import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { GenomicScoreInterface } from 'app/genotype-browser/genotype-browser';
import { reset } from 'app/users/state-actions';
import { cloneDeep } from 'lodash';

export const initialState: GenomicScoreInterface[] = [];

export const selectGenomicScores = createFeatureSelector<GenomicScoreInterface[]>('genomicScores');

export const setGenomicScores = createAction(
  '[Genotype] Set genomic scores',
  props<{ genomicScores: GenomicScoreInterface[] }>()
);

export const resetGenomicScores = createAction(
  '[Genotype] Reset genomic scores'
);

export const genomicScoresReducer = createReducer(
  initialState,
  on(setGenomicScores, (state, {genomicScores}) => cloneDeep(genomicScores)),
  on(reset, resetGenomicScores, state => cloneDeep(initialState)),
);
