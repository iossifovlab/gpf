import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
export const initialState = [];

export const selectGenders = createFeatureSelector<string[]>('genders');

export const setGenders = createAction(
  '[Genotype] Set gedners',
  props<{ genders: string[] }>()
);

export const addGender = createAction(
  '[Genotype] Add gender',
  props<{ gender: string }>()
);

export const removeGender = createAction(
  '[Genotype] Remove gender',
  props<{ gender: string }>()
);

export const resetGenders = createAction(
  '[Genotype] Reset genders'
);

export const gendersReducer = createReducer(
  initialState,
  on(setGenders, (state: string[], {genders}) => [...genders]),
  on(addGender, (state: string[], {gender}) => [...state, gender]),
  on(removeGender, (state: string[], {gender}) => state.filter(gen => gen !== gender)),
  on(reset, resetGenders, state => [...initialState]),
);
