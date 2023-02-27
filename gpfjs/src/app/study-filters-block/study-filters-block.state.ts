import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetStudyFilters {
  public static readonly type = '[Genotype] Set studyFilters';
  public constructor(public studyFilters: string[]) {}
}

export interface StudyFiltersBlockModel {
  studyFilters: string[];
}

@State<StudyFiltersBlockModel>({
  name: 'studyFiltersBlockState',
  defaults: {
    studyFilters: []
  },
})
@Injectable()
export class StudyFiltersBlockState {
  @Action(SetStudyFilters)
  public setStudyFilters(ctx: StateContext<StudyFiltersBlockModel>, action: SetStudyFilters): void {
    ctx.patchState({
      studyFilters: [...action.studyFilters]
    });
  }
}
