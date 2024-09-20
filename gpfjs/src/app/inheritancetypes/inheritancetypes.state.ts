import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
export const initialState: string[] = [];

export const selectInheritanceTypes = createFeatureSelector<string[]>('inheritanceTypes');

export const setInheritanceTypes = createAction(
  '[Genotype] Set inheritance type values',
  props<{ inheritanceTypes: string[] }>()
);

export const resetInheritanceTypes = createAction(
  '[Genotype] Reset inheritance type'
);

export const inheritanceTypesReducer = createReducer(
  initialState,
  on(setInheritanceTypes, (state: string[], {inheritanceTypes}) => [...inheritanceTypes]),
  on(reset, resetInheritanceTypes, state => [...initialState]),
);
