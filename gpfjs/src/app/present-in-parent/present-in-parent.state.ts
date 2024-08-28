import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';

export interface PresentInParent {
  presentInParent: string[];
  rarityType: string;
  rarityIntervalStart: number;
  rarityIntervalEnd: number;
}

export const initialState: PresentInParent = {
  presentInParent: ['neither'],
  rarityType: '',
  rarityIntervalStart: 0,
  rarityIntervalEnd: 1,
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
  on(resetPresentInParent, state => cloneDeep(initialState)),
);
