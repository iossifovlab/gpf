import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
import { HistogramType, CategoricalHistogramView } from 'app/utils/histogram-types';
import { cloneDeep } from 'lodash';

export interface GenomicScoreState {
  histogramType: HistogramType;
  score: string;
  rangeStart: number;
  rangeEnd: number;
  values: string[];
  categoricalView: CategoricalHistogramView;
}

export const initialState: GenomicScoreState[] = [];


export const selectGenomicScores = createFeatureSelector<GenomicScoreState[]>('genomicScores');

export const setGenomicScores = createAction(
  '[Genotype] Set genomic scores',
  props<{ genomicScores: GenomicScoreState[] }>()
);

export const setGenomicScoresContinuous = createAction(
  '[Genotype] Set genomic score with continuous histogram data',
  props<{score: string, rangeStart: number, rangeEnd: number}>()
);

export const setGenomicScoresCategorical = createAction(
  '[Genotype] Set genomic score with categorical histogram data',
  props<{score: string, values: string[], categoricalView: CategoricalHistogramView}>()
);

export const removeGenomicScore = createAction(
  '[Genotype] Remove genomic score with histogram data',
  props<{genomicScoreName: string}>()
);

export const resetGenomicScores = createAction(
  '[Genotype] Reset genomic scores'
);

export const genomicScoresReducer = createReducer(
  initialState,
  on(setGenomicScores, (state, {genomicScores}) => cloneDeep(genomicScores)),
  on(setGenomicScoresContinuous, (state, { score, rangeStart, rangeEnd }) => {
    const newGenomicScore = {
      histogramType: 'continuous' as const,
      score: score,
      rangeStart: rangeStart,
      rangeEnd: rangeEnd,
      values: null,
      categoricalView: null,
    };
    const scores = [...state];
    const scoreIndex = scores.findIndex(s => s.score === score);
    if (!scores.length || scoreIndex === -1) {
      scores.push(newGenomicScore);
    } else {
      const scoreCopy = cloneDeep(scores.at(scoreIndex));
      scoreCopy.rangeStart = rangeStart;
      scoreCopy.rangeEnd = rangeEnd;
      scores[scoreIndex] = scoreCopy;
    }
    return scores;
  }),
  on(setGenomicScoresCategorical, (state, { score, values, categoricalView }) => {
    const newGenomicScore = {
      histogramType: 'categorical' as const,
      score: score,
      rangeStart: null,
      rangeEnd: null,
      values: values,
      categoricalView: categoricalView,
    };
    const scores = [...state];
    const scoreIndex = scores.findIndex(s => s.score === score);
    if (!scores.length || scoreIndex === -1) {
      scores.push(newGenomicScore);
    } else {
      const scoreCopy = cloneDeep(scores.at(scoreIndex));
      scoreCopy.values = values;
      scoreCopy.categoricalView = categoricalView;
      scores[scoreIndex] = scoreCopy;
    }
    return scores;
  }),
  on(removeGenomicScore, (state, {genomicScoreName}) => {
    return [...state].filter(score => score.score !== genomicScoreName);
  }),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetGenomicScores, state => cloneDeep(initialState)),
);
