import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
import { cloneDeep } from 'lodash';

export const initialState: string[] = ['we', 'wg', 'tg'];

export const selectStudyTypes = createFeatureSelector<string[]>('studyTypes');

export const setStudyTypes = createAction(
  '[Genotype] Set study type',
  props<{ studyTypes: string[] }>()
);

export const resetStudyTypes = createAction(
  '[Genotype] Reset study type'
);

export const studyTypesReducer = createReducer(
  initialState,
  on(setStudyTypes, (state: string[], {studyTypes}) => cloneDeep(studyTypes)),
  on(reset, resetStudyTypes, state => cloneDeep(initialState)),
);
