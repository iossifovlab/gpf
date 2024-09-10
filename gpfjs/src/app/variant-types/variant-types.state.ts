import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { logout } from 'app/users/actions';
import { cloneDeep } from 'lodash';

export const initialState: string[] = null;

export const selectVariantTypes = createFeatureSelector<string[]>('variantTypes');

export const setVariantTypes = createAction(
  '[Genotype] Set variant types',
  props<{ variantTypes: string[] }>()
);

export const resetVariantTypes = createAction(
  '[Genotype] Reset variant types'
);

export const variantTypesReducer = createReducer(
  initialState,
  on(setVariantTypes, (state, {variantTypes}) => [...variantTypes]),
  on(logout, resetVariantTypes, state => cloneDeep(initialState)),
);
