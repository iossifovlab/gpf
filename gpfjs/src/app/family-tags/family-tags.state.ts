import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = {};

export const selectFamilyTags = createFeatureSelector<object>('familyTags');

export const setFamilyTags = createAction(
  '[Genotype] Set family tags',
  props<{ selectedFamilyTags: string[]; deselectedFamilyTags: string[]; tagIntersection: boolean }>()
);

export const familyTagsReducer = createReducer(
  initialState,
  on(
    setFamilyTags,
    (state, { selectedFamilyTags, deselectedFamilyTags, tagIntersection }) => ({
      selectedFamilyTags: selectedFamilyTags,
      deselectedFamilyTags: deselectedFamilyTags,
      tagIntersection: tagIntersection,
    })
  )
);
