import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetStudyFilters {
  public static readonly type = '[Genotype] Set studyFilters';
  public constructor(public studyFilters: string[]) {}
}

export interface StudyFiltersModel {
  studyFilters: string[];
}

@State<StudyFiltersModel>({
  name: 'studyFiltersState',
  defaults: {
    studyFilters: []
  },
})
@Injectable()
export class StudyFiltersState {
  @Action(SetStudyFilters)
  public setStudyFilters(ctx: StateContext<StudyFiltersModel>, action: SetStudyFilters): void {
    ctx.patchState({
      studyFilters: [...action.studyFilters]
    });
  }
}
