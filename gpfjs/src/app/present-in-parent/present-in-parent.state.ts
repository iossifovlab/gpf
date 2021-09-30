import { Injectable } from '@angular/core';
import { State, Action, StateContext, Selector } from '@ngxs/store';

export class SetPresentInParentValues {
  static readonly type = '[Genotype] Set presentInParent values';
  constructor(
    public presentInParent: Set<string>,
    public rarityType: string,
    public rarityIntervalStart: number,
    public rarityIntervalEnd: number,
  ) {}
}

export interface PresentInParentModel {
  presentInParent: string[];
  rarityType: string;
  rarityIntervalStart: number;
  rarityIntervalEnd: number;
}

@State<PresentInParentModel>({
  name: 'presentInParentState',
  defaults: {
    presentInParent: ['neither'],
    rarityType: '',
    rarityIntervalStart: 0,
    rarityIntervalEnd: 1,
  },
})
@Injectable()
export class PresentInParentState {
  @Action(SetPresentInParentValues)
  setPresentInParentValue(ctx: StateContext<PresentInParentModel>, action: SetPresentInParentValues) {
    const state = ctx.getState();
    ctx.patchState({
      presentInParent: [...action.presentInParent],
      rarityType: action.rarityType,
      rarityIntervalStart: action.rarityIntervalStart,
      rarityIntervalEnd: action.rarityIntervalEnd,
    });
  }

  @Selector([PresentInParentState])
  static queryStateSelector(state: PresentInParentModel) {
    const res = {
      'presentInParent': state.presentInParent
    };
    if (state.presentInParent.length === 1 && state.presentInParent[0] === 'neither') {
      return res;
    }
    res['rarity'] = { 'ultraRare': state.rarityType === 'ultraRare' };
    if (state.rarityType !== 'ultraRare' && state.rarityType !== 'all') {
      res['rarity']['minFreq'] = state.rarityIntervalStart;
      res['rarity']['maxFreq'] = state.rarityIntervalEnd;
    }
    return res;
  }
}
