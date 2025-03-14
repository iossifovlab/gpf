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
  roles: string[]
}

export const measureHistogramInitialState: MeasureHistogramState[] = [];

export const selectFamilyMeasureHistograms = createFeatureSelector<MeasureHistogramState[]>('familyMeasureHistograms');

export const setFamilyMeasureHistograms = createAction(
  '[Genotype] Set family measure histograms',
  props<{ familyMeasureHistograms: MeasureHistogramState[] }>()
);

export const setFamilyMeasureHistogramsContinuous = createAction(
  '[Genotype] Set family measure histogram with continuous histogram data',
  props<{measure: string, rangeStart: number, rangeEnd: number, roles: string[]}>()
);

export const setFamilyMeasureHistogramsCategorical = createAction(
  '[Genotype] Set family measure histogram with categorical histogram data',
  props<{measure: string, values: string[], categoricalView: CategoricalHistogramView, roles: string[]}>()
);

export const removeFamilyMeasureHistogram = createAction(
  '[Genotype] Remove family measure histogram',
  props<{familyMeasureHistogramName: string}>()
);

export const resetFamilyMeasureHistograms = createAction(
  '[Genotype] Reset family measure histograms'
);

export const familyMeasureHistogramsReducer = createReducer(
  measureHistogramInitialState,
  on(setFamilyMeasureHistograms, (state, {familyMeasureHistograms}) => cloneDeep(familyMeasureHistograms)),
  on(setFamilyMeasureHistogramsContinuous, (state, { measure, rangeStart, rangeEnd, roles }) => {
    const newMeasureHistogram = {
      histogramType: 'continuous' as const,
      measure: measure,
      rangeStart: rangeStart,
      rangeEnd: rangeEnd,
      values: null,
      categoricalView: null,
      roles: null
    };
    const measureHistograms = [...state];
    const histogramIndex = measureHistograms.findIndex(h => h.measure === measure);
    if (!measureHistograms.length || histogramIndex === -1) {
      measureHistograms.push(newMeasureHistogram);
    } else {
      const histogramCopy = cloneDeep(measureHistograms.at(histogramIndex));
      histogramCopy.rangeStart = rangeStart;
      histogramCopy.rangeEnd = rangeEnd;
      histogramCopy.roles = roles;
      measureHistograms[histogramIndex] = histogramCopy;
    }
    return measureHistograms;
  }),
  on(setFamilyMeasureHistogramsCategorical, (state, { measure, values, categoricalView, roles }) => {
    const newMeasureHistogram = {
      histogramType: 'categorical' as const,
      measure: measure,
      rangeStart: null,
      rangeEnd: null,
      values: values,
      categoricalView: categoricalView,
      roles: null
    };
    const measureHistograms = [...state];
    const histogramIndex = measureHistograms.findIndex(h => h.measure === measure);
    if (!measureHistograms.length || histogramIndex === -1) {
      measureHistograms.push(newMeasureHistogram);
    } else {
      const histogramCopy = cloneDeep(measureHistograms.at(histogramIndex));
      histogramCopy.values = values;
      histogramCopy.categoricalView = categoricalView;
      histogramCopy.roles = roles;
      measureHistograms[histogramIndex] = histogramCopy;
    }
    return measureHistograms;
  }),
  on(removeFamilyMeasureHistogram, (state, {familyMeasureHistogramName}) => {
    return [...state].filter(histogram => histogram.measure !== familyMeasureHistogramName);
  }),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetFamilyMeasureHistograms, state => cloneDeep(measureHistogramInitialState)),
);


export const selectPersonMeasureHistograms = createFeatureSelector<MeasureHistogramState[]>('personMeasureHistograms');

export const setPersonMeasureHistograms = createAction(
  '[Genotype] Set person measure histograms',
  props<{ personMeasureHistograms: MeasureHistogramState[] }>()
);

export const setPersonMeasureHistogramsContinuous = createAction(
  '[Genotype] Set person measure histogram with continuous histogram data',
  props<{measure: string, rangeStart: number, rangeEnd: number, roles: string[]}>()
);

export const setPersonMeasureHistogramsCategorical = createAction(
  '[Genotype] Set person measure histogram with categorical histogram data',
  props<{measure: string, values: string[], categoricalView: CategoricalHistogramView, roles: string[]}>()
);

export const removePersonMeasureHistogram = createAction(
  '[Genotype] Remove person measure histogram',
  props<{personMeasureHistogramName: string}>()
);

export const resetPersonMeasureHistograms = createAction(
  '[Genotype] Reset person measure histograms'
);

export const personMeasureHistogramsReducer = createReducer(
  measureHistogramInitialState,
  on(setPersonMeasureHistograms, (state, {personMeasureHistograms}) => cloneDeep(personMeasureHistograms)),
  on(setPersonMeasureHistogramsContinuous, (state, { measure, rangeStart, rangeEnd, roles }) => {
    const newMeasureHistogram = {
      histogramType: 'continuous' as const,
      measure: measure,
      rangeStart: rangeStart,
      rangeEnd: rangeEnd,
      values: null,
      categoricalView: null,
      roles: null
    };
    const measureHistograms = [...state];
    const histogramIndex = measureHistograms.findIndex(h => h.measure === measure);
    if (!measureHistograms.length || histogramIndex === -1) {
      measureHistograms.push(newMeasureHistogram);
    } else {
      const histogramCopy = cloneDeep(measureHistograms.at(histogramIndex));
      histogramCopy.rangeStart = rangeStart;
      histogramCopy.rangeEnd = rangeEnd;
      histogramCopy.roles = roles;
      measureHistograms[histogramIndex] = histogramCopy;
    }
    return measureHistograms;
  }),
  on(setPersonMeasureHistogramsCategorical, (state, { measure, values, categoricalView, roles }) => {
    const newMeasureHistogram = {
      histogramType: 'categorical' as const,
      measure: measure,
      rangeStart: null,
      rangeEnd: null,
      values: values,
      categoricalView: categoricalView,
      roles: null
    };
    const measureHistograms = [...state];
    const histogramIndex = measureHistograms.findIndex(h => h.measure === measure);
    if (!measureHistograms.length || histogramIndex === -1) {
      measureHistograms.push(newMeasureHistogram);
    } else {
      const histogramCopy = cloneDeep(measureHistograms.at(histogramIndex));
      histogramCopy.values = values;
      histogramCopy.categoricalView = categoricalView;
      histogramCopy.roles = roles;
      measureHistograms[histogramIndex] = histogramCopy;
    }
    return measureHistograms;
  }),
  on(removePersonMeasureHistogram, (state, {personMeasureHistogramName}) => {
    return [...state].filter(histogram => histogram.measure !== personMeasureHistogramName);
  }),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetPersonMeasureHistograms, state => cloneDeep(measureHistogramInitialState)),
);