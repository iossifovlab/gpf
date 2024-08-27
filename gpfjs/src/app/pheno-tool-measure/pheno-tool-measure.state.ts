import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';

export interface PhenoToolMeasure {
  measureId: string;
  normalizeBy: object[];
}

export const initialState: PhenoToolMeasure = {
  measureId: '',
  normalizeBy: []
};

export const selectPhenoToolMeasure = createFeatureSelector<PhenoToolMeasure>('phenoToolMeasure');

export const setPhenoToolMeasure = createAction(
  '[Phenotype] Set phenoToolMeasure values',
  props<{ phenoToolMeasure: PhenoToolMeasure }>()
);

export const resetPhenoToolMeasure = createAction(
  '[Phenotype] Reset phenoToolMeasure values'
);

export const phenoToolMeasureReducer = createReducer(
  initialState,
  on(setPhenoToolMeasure, (state, { phenoToolMeasure }) => cloneDeep(phenoToolMeasure)),
  on(resetPhenoToolMeasure, state => cloneDeep(initialState)),
);
