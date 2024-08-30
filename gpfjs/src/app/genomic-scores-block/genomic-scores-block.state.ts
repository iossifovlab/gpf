import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { GenomicScoreInterface } from 'app/genotype-browser/genotype-browser';
import { cloneDeep } from 'lodash';

export const initialState: GenomicScoreInterface[] = [{
  metric: '',
  rangeStart: null,
  rangeEnd: null,
}];

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
  on(resetGenomicScores, state => cloneDeep(initialState)),
);
