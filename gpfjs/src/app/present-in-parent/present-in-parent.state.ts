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
  rarityIntervalStart: 0,
  rarityIntervalEnd: 1,
};

export const initialState: PresentInParent = {
  presentInParent: ['neither'],
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
  on(setPresentInParent, (state: PresentInParent, {presentInParent}) => cloneDeep(presentInParent)),
  on(reset, resetPresentInParent, state => cloneDeep(initialState)),
);
