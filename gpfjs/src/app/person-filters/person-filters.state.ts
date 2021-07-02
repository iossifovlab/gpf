import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPersonFilters {
  static readonly type = '[Genotype] Set personFilters values';
  constructor(public filterType: string, public filters: object[]) {}
}

export interface PersonFiltersModel {
  filterType: string; // Whether this is a family or person filter
  filters: object[];
}

@State<PersonFiltersModel>({
  name: 'personFiltersState',
  defaults: {
    filterType: '',
    filters: []
  },
})
@Injectable()
export class PersonFiltersState {
  @Action(SetPersonFilters)
  setInheritanceTypes(ctx: StateContext<PersonFiltersModel>, action: SetPersonFilters) {
    ctx.patchState({
      filterType: action.filterType,
      filters: {...action.filters}
    });
  }
}
