import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetFamilyFilters {
  static readonly type = '[Genotype] Set familyFiltes values';
  constructor(public filters: object[]) {}
}

export class SetPersonFilters {
  static readonly type = '[Genotype] Set personFilters values';
  constructor(public filters: object[]) {}
}

export interface PersonFiltersModel {
  familyFilters: object[];
  personFilters: object[];
}

@State<PersonFiltersModel>({
  name: 'personFiltersState',
  defaults: {
    familyFilters: [],
    personFilters: [],
  },
})
@Injectable()
export class PersonFiltersState {
  @Action(SetFamilyFilters)
  setFamilyFilters(ctx: StateContext<PersonFiltersModel>, action: SetFamilyFilters) {
    ctx.patchState({
      familyFilters: [...action.filters],
    });
  }

  @Action(SetPersonFilters)
  setPersonFilters(ctx: StateContext<PersonFiltersModel>, action: SetPersonFilters) {
    ctx.patchState({
      personFilters: [...action.filters],
    });
  }
}
