import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetStudyTypes {
  static readonly type = '[Genotype] Set studyTypes values';
  constructor(public studyTypes: Set<string>) {}
}

export interface StudyTypesModel {
  studyTypes: string[];
}

@State<StudyTypesModel>({
  name: 'studyTypesState',
  defaults: {
    studyTypes: []
  },
})
@Injectable()
export class StudyTypesState {
  @Action(SetStudyTypes)
  setStudyTypesValue(ctx: StateContext<StudyTypesModel>, action: SetStudyTypes) {
    ctx.patchState({
      studyTypes: [...action.studyTypes]
    });
  }
}
