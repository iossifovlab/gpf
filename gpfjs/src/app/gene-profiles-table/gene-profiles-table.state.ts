import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetGeneProfiles {
  public static readonly type = '[Genotype] Set gene profiles';
  public constructor(
    public openedTabs: Set<string>
  ) {}
}

export interface GeneProfilesModel {
  openedTabs: Set<string>;
}

@State<GeneProfilesModel>({
  name: 'geneProfilesState',
  defaults: {
    openedTabs: new Set<string>()
  },
})
@Injectable()
export class GeneProfilesState {
  @Action(SetGeneProfiles)
  public setGeneProfiles(ctx: StateContext<GeneProfilesModel>, action: SetGeneProfiles): void {
    ctx.patchState({
      openedTabs: action.openedTabs,
    });
  }
}
