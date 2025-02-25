import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { FamilyTags } from './family-tags';
import { cloneDeep } from 'lodash';
import { reset } from 'app/users/state-actions';

export const initialState: FamilyTags = {
  selectedFamilyTags: [],
  deselectedFamilyTags: [],
  tagIntersection: true,
};

export const selectFamilyTags = createFeatureSelector<FamilyTags>('familyTags');

export const setFamilyTags = createAction(
  '[Genotype] Set family tags',
  props<FamilyTags>()
);

export const resetFamilyTags = createAction(
  '[Genotype] Reset family tags'
);

export const familyTagsReducer = createReducer(
  initialState,
  on(
    setFamilyTags,
    (state, { selectedFamilyTags, deselectedFamilyTags, tagIntersection }) => cloneDeep({
      selectedFamilyTags: selectedFamilyTags,
      deselectedFamilyTags: deselectedFamilyTags,
      tagIntersection: tagIntersection,
    })
  ),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetFamilyTags, state => cloneDeep(initialState)),
);
