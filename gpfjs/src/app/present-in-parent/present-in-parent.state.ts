import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
import { cloneDeep } from 'lodash';

export interface PresentInParentRarity {
  rarityType: string;
  rarityIntervalStart: number;
  rarityIntervalEnd: number;
}

export interface PresentInParent {
  presentInParent: string[];
  rarity: PresentInParentRarity;
}

const initialRarityState: PresentInParentRarity = {
  rarityType: '',
  rarityIntervalStart: null,
  rarityIntervalEnd: null,
};

export const initialState: PresentInParent = {
  presentInParent: [],
  rarity: initialRarityState
};

export const selectPresentInParent = createFeatureSelector<PresentInParent>('presentInParent');

export const setPresentInParent = createAction(
  '[Genotype] Set present in parent',
  props<{ presentInParent: PresentInParent }>()
);

export const resetPresentInParent = createAction(
  '[Genotype] Reset present in parent'
);

export const presentInParentReducer = createReducer(
  initialState,
  on(setPresentInParent, (state: PresentInParent, {presentInParent}) => {
    state = cloneDeep(presentInParent);
    // Rare can't have start value
    if (state.rarity.rarityType === 'rare') {
      state.rarity.rarityIntervalStart = null;
    }
    return state;
  }),
  on(reset, resetPresentInParent, state => cloneDeep(initialState)),
);
