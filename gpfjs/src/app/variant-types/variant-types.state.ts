import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState: string[] = [];

export const selectVariantTypes = createFeatureSelector<string[]>('variantTypes');

export const setVariantTypes = createAction(
  '[Genotype] Set variant types',
  props<{ variantTypes: string[] }>()
);

export const resetVariantTypes = createAction(
  '[Genotype] Reset family ids'
);

export const variantTypesReducer = createReducer(
  initialState,
  on(setVariantTypes, (state, {variantTypes}) => [...variantTypes]),
  on(resetVariantTypes, state => []),
);
