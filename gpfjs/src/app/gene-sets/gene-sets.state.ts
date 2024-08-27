import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { GeneSet, GeneSetsCollection, GeneSetType } from './gene-sets';
export const initialState: { geneSetsTypes: object; geneSetsCollection: object; geneSet: object } = {
  geneSetsTypes: null,
  geneSetsCollection: null,
  geneSet: null
};

export const selectGeneSets =
  createFeatureSelector<{
    geneSetsTypes: GeneSetType[];
    geneSetsCollection: GeneSetsCollection;
    geneSet: GeneSet;
  }>('geneSets');

export const setGeneSetsValues = createAction(
  '[Genotype] Set geneSets values',
  props<{ geneSetsTypes: GeneSetType[]; geneSetsCollection: GeneSetsCollection; geneSet: GeneSet }>()
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
  on(getGeneSetsValues, (state) => cloneDeep(state)),
  on(resetGeneSetsValues, state => cloneDeep(initialState)),
);
