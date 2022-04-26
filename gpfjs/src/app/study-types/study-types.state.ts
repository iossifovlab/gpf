import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetStudyTypes {
  public static readonly type = '[Genotype] Set studyTypes values';
  public constructor(public studyTypes: Set<string>) {}
}

export interface StudyTypesModel {
  studyTypes: string[];
}

@State<StudyTypesModel>({
  name: 'studyTypesState',
  defaults: {
    studyTypes: ['we', 'wg', 'tg']
  },
})
@Injectable()
export class StudyTypesState {
  @Action(SetStudyTypes)
  public setStudyTypesValue(ctx: StateContext<StudyTypesModel>, action: SetStudyTypes): void {
    ctx.patchState({
      studyTypes: [...action.studyTypes]
    });
  }
}
