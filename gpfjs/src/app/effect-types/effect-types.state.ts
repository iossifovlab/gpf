import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState: string[] = [];

export const selectEffectTypes = createFeatureSelector<string[]>('effectTypes');

export const setEffectTypes = createAction(
  '[Genotype] Set effect types',
  props<{ effectTypes: string[] }>()
);

export const addEffectType = createAction(
  '[Genotype] Add EffectType',
  props<{ effectType: string }>()
);

export const removeEffectType = createAction(
  '[Genotype] Remove EffectType',
  props<{ effectType: string }>()
);

export const resetEffectTypes = createAction(
  '[Genotype] Reset effect types'
);

export const effectTypesReducer = createReducer(
  initialState,
  on(setEffectTypes, (state: string[], {effectTypes}) => [...effectTypes]),
  on(addEffectType, (state: string[], {effectType}) => [...state, effectType]),
  on(addEffectType, (state: string[], {effectType}) => state.filter(eff => eff !== effectType)),
  on(resetEffectTypes, state => [...initialState]),
);
