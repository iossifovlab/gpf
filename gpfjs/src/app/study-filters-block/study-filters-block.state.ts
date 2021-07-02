import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetStudyFilters {
  static readonly type = '[Genotype] Set studyFilters';
  constructor(public studyFilters: string[]) {}
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
  setStudyFilters(ctx: StateContext<StudyFiltersBlockModel>, action: SetStudyFilters) {
    ctx.patchState({
      studyFilters: [...action.studyFilters]
    });
  }
}
