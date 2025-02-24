import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
import { HistogramType, CategoricalHistogramView } from 'app/utils/histogram-types';
import { cloneDeep } from 'lodash';

export interface MeasureHistogramState {
  histogramType: HistogramType;
  measure: string;
  rangeStart: number;
  rangeEnd: number;
  values: string[];
  categoricalView: CategoricalHistogramView;
}

export const initialState: MeasureHistogramState[] = [];


export const selectMeasureHistograms = createFeatureSelector<MeasureHistogramState[]>('measureHistograms');

export const setMeasureHistograms = createAction(
  '[Genotype] Set measure histograms',
  props<{ measureHistograms: MeasureHistogramState[] }>()
);

export const setMeasureHistogramsContinuous = createAction(
  '[Genotype] Set measure histogram with continuous histogram data',
  props<{measure: string, rangeStart: number, rangeEnd: number}>()
);

export const setMeasureHistogramsCategorical = createAction(
  '[Genotype] Set measure histogram with categorical histogram data',
  props<{measure: string, values: string[], categoricalView: CategoricalHistogramView}>()
);

export const removeMeasureHistogram = createAction(
  '[Genotype] Remove measure histogram with histogram data',
  props<{measureHistogramName: string}>()
);

export const resetMeasureHistograms = createAction(
  '[Genotype] Reset measure histograms'
);

export const measureHistogramsReducer = createReducer(
  initialState,
  on(setMeasureHistograms, (state, {measureHistograms}) => cloneDeep(measureHistograms)),
  on(setMeasureHistogramsContinuous, (state, { measure, rangeStart, rangeEnd }) => {
    const newMeasureHistogram = {
      histogramType: 'continuous' as const,
      measure: measure,
      rangeStart: rangeStart,
      rangeEnd: rangeEnd,
      values: null,
      categoricalView: null,
    };
    const measureHistograms = [...state];
    const histogramIndex = measureHistograms.findIndex(h => h.measure === measure);
    if (!measureHistograms.length || histogramIndex === -1) {
      measureHistograms.push(newMeasureHistogram);
    } else {
      const histogramCopy = cloneDeep(measureHistograms.at(histogramIndex));
      histogramCopy.rangeStart = rangeStart;
      histogramCopy.rangeEnd = rangeEnd;
      measureHistograms[histogramIndex] = histogramCopy;
    }
    return measureHistograms;
  }),
  on(setMeasureHistogramsCategorical, (state, { measure, values, categoricalView }) => {
    const newMeasureHistogram = {
      histogramType: 'categorical' as const,
      measure: measure,
      rangeStart: null,
      rangeEnd: null,
      values: values,
      categoricalView: categoricalView,
    };
    const measureHistograms = [...state];
    const histogramIndex = measureHistograms.findIndex(h => h.measure === measure);
    if (!measureHistograms.length || histogramIndex === -1) {
      measureHistograms.push(newMeasureHistogram);
    } else {
      const histogramCopy = cloneDeep(measureHistograms.at(histogramIndex));
      histogramCopy.values = values;
      histogramCopy.categoricalView = categoricalView;
      measureHistograms[histogramIndex] = histogramCopy;
    }
    return measureHistograms;
  }),
  on(removeMeasureHistogram, (state, {measureHistogramName}) => {
    return [...state].filter(histogram => histogram.measure !== measureHistogramName);
  }),
  on(reset, resetMeasureHistograms, state => cloneDeep(initialState)),
);
