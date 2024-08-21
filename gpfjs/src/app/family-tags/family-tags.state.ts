// import { Injectable } from '@angular/core';
// import { State, Action, StateContext } from '@ngxs/store';

// export class SetFamilyTags {
//   public static readonly type = '[Genotype] Set family tags';
//   public constructor(
//     public selectedFamilyTags: string[],
//     public deselectedFamilyTags: string[],
//     public tagIntersection: boolean
//   ) {}
// }

// export interface FamilyTagsModel {
//   selectedFamilyTags: string[];
//   deselectedFamilyTags: string[];
//   tagIntersection: boolean;
// }

// @State<FamilyTagsModel>({
//   name: 'familyTagsState',
//   defaults: {
//     selectedFamilyTags: [],
//     deselectedFamilyTags: [],
//     tagIntersection: true
//   },
// })
// @Injectable()
// export class FamilyTagsState {
//   @Action(SetFamilyTags)
//   public changeFamilyTags(ctx: StateContext<FamilyTagsModel>, action: SetFamilyTags): void {
//     ctx.patchState({
//       selectedFamilyTags: action.selectedFamilyTags,
//       deselectedFamilyTags: action.deselectedFamilyTags,
//       tagIntersection: action.tagIntersection
//     });
//   }
// }


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
