import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';

export const initialState: string[] = [];

export const selectPresentInChild = createFeatureSelector<string[]>('presentInChild');

export const setPresentInChild = createAction(
  '[Genotype] Set present in child',
  props<{ presentInChild: string[] }>()
);

export const resetPresentInChild = createAction(
  '[Genotype] Reset present in child'
);

export const presentInChildReducer = createReducer(
  initialState,
  on(setPresentInChild, (state: string[], {presentInChild}) => [...presentInChild]),
  on(reset, resetPresentInChild, state => [...initialState]),
);
