import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { reset } from 'app/users/state-actions';
import { CategoricalHistogramView } from 'app/genomic-scores-block/genomic-scores-block';


export type HistogramType = 'continuous' | 'categorical';

export interface GeneScoresState {
  histogramType: HistogramType;
  score: string;
  rangeStart: number;
  rangeEnd: number;
  values: string[];
  categoricalView: CategoricalHistogramView;
}

export const initialState: GeneScoresState = {
  histogramType: null,
  score: null,
  rangeStart: 0,
  rangeEnd: 0,
  values: null,
  categoricalView: null,
};

export const selectGeneScores =
  createFeatureSelector<GeneScoresState>('geneScores');

export const setGeneScoreContinuous = createAction(
  '[Genotype] Set score with continuous histogram data',
  props<{score: string, rangeStart: number, rangeEnd: number}>()
);

export const setGeneScoreCategorical = createAction(
  '[Genotype] Set score with categorical histogram data',

  props<{score: string, values: string[], categoricalView: CategoricalHistogramView}>()
);

export const resetGeneScoresValues = createAction(
  '[Genotype] Reset geneScores values'
);

export const geneScoresReducer = createReducer(
  initialState,
  on(setGeneScoreContinuous, (state, { score, rangeStart, rangeEnd }) => ({
    histogramType: 'continuous' as const,
    score: score,
    rangeStart: rangeStart,
    rangeEnd: rangeEnd,
    values: initialState.values,
    categoricalView: initialState.categoricalView,
  })),
  on(setGeneScoreCategorical, (state, { score, values, categoricalView }) => ({
    histogramType: 'categorical' as const,
    score: score,
    rangeStart: initialState.rangeStart,
    rangeEnd: initialState.rangeEnd,
    values: values,
    categoricalView: categoricalView,
  })),
  on(reset, resetGeneScoresValues, state => cloneDeep(initialState))
);
