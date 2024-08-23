import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
export const initialState: { geneSetsTypes: object; geneSetsCollection: object; geneSet: object } = {
  geneSetsTypes: null,
  geneSetsCollection: null,
  geneSet: null
};

export const selectGeneSets =
  createFeatureSelector<{ geneSetsTypes: object; geneSetsCollection: object; geneSet: object }>('geneSets');

export const setGeneSetsValues = createAction(
  '[Genotype] Set geneSets values',
  props<{ geneSetsTypes: object; geneSetsCollection: object; geneSet: object }>()
);

export const getGeneSetsValues = createAction(
  '[Genotype] Set geneSets values');

export const resetGeneSetsValues = createAction(
  '[Genotype] Reset geneSets values'
);

export const geneSetsReducer = createReducer(
  initialState,
  on(setGeneSetsValues, (state, { geneSetsTypes, geneSetsCollection, geneSet }) => ({
    geneSetsTypes: cloneDeep(geneSetsTypes),
    geneSetsCollection: cloneDeep(geneSetsCollection),
    geneSet: cloneDeep(geneSet)
  })),
  on(getGeneSetsValues, (state) => ({
    geneSet: state.geneSet['name'],
    geneSetsCollection: state.geneSetsCollection['name'],
    geneSetsTypes: cloneDeep(state.geneSetsTypes),
  })),
  on(resetGeneSetsValues, state => cloneDeep(initialState)),
);
