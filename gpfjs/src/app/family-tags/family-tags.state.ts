import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetFamilyTags {
  public static readonly type = '[Genotype] Set family tags';
  public constructor(
    public selectedFamilyTags: string[],
    public deselectedFamilyTags: string[],
    public tagIntersection: boolean
  ) {}
}

export interface FamilyTagsModel {
  selectedFamilyTags: string[];
  deselectedFamilyTags: string[];
  tagIntersection: boolean;
}

@State<FamilyTagsModel>({
  name: 'familyTagsState',
  defaults: {
    selectedFamilyTags: [],
    deselectedFamilyTags: [],
    tagIntersection: true
  },
})
@Injectable()
export class FamilyTagsState {
  @Action(SetFamilyTags)
  public changeFamilyTags(ctx: StateContext<FamilyTagsModel>, action: SetFamilyTags): void {
    ctx.patchState({
      selectedFamilyTags: action.selectedFamilyTags,
      deselectedFamilyTags: action.deselectedFamilyTags,
      tagIntersection: action.tagIntersection
    });
  }
}
