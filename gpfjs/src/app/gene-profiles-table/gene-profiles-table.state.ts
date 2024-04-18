import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';
import { GeneProfilesTableConfig } from './gene-profiles-table';

export class SetGeneProfiles {
  public static readonly type = '[Genotype] Set gene profiles';
  public constructor(
    public openedTabs: Set<string>,
    public searchValue: string,
    public highlightedRows: Set<string>,
    public sortBy: string,
    public orderBy: string,
    public config: GeneProfilesTableConfig
  ) {}
}

export interface GeneProfilesModel {
    openedTabs: Set<string>;
    searchValue: string;
    highlightedRows: Set<string>;
    sortBy: string;
    orderBy: string;
    config: GeneProfilesTableConfig;
}

@State<GeneProfilesModel>({
  name: 'geneProfilesState',
  defaults: {
    openedTabs: new Set<string>(),
    searchValue: '',
    highlightedRows: new Set<string>(),
    sortBy: '',
    orderBy: '',
    config: null
  },
})
@Injectable()
export class GeneProfilesState {
  @Action(SetGeneProfiles)
  public setGeneProfiles(ctx: StateContext<GeneProfilesModel>, action: SetGeneProfiles): void {
    ctx.patchState({
      openedTabs: action.openedTabs,
      searchValue: action.searchValue,
      highlightedRows: action.highlightedRows,
      sortBy: action.sortBy,
      orderBy: action.orderBy,
      config: action.config
    });
  }
}
