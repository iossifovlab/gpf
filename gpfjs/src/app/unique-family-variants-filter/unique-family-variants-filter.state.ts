import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { logout } from 'app/users/actions';

export const initialState = false;

export const selectUniqueFamilyVariantsFilter = createFeatureSelector<boolean>('uniqueFamilyVariantsFilter');

export const setUniqueFamilyVariantsFilter = createAction(
  '[Genotype] Set unique family variants filter',
  props<{ uniqueFamilyVariantsFilter: boolean }>()
);

export const resetUniqueFamilyVariantsFilter = createAction(
  '[Genotype] Reset unique family variants filter'
);

export const uniqueFamilyVariantsFilterReducer = createReducer(
  initialState,
  on(setUniqueFamilyVariantsFilter, (state, {uniqueFamilyVariantsFilter}) => uniqueFamilyVariantsFilter),
  on(logout, resetUniqueFamilyVariantsFilter, state => initialState),
);
