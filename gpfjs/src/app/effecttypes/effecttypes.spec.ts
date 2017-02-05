/**
 * New typescript file
 */


import {
  EFFECT_TYPE_CHECK,
  EFFECT_TYPE_UNCHECK,
  effectTypesReducer
} from './effecttypes';


describe('EffectTypesReducer', () => {
  it('checknig effect type should add it', () => {
    let initialState = [];
    let finalState = ['Nonsense'];
    let action = { type: EFFECT_TYPE_CHECK, payload: 'Nonsense' };

    let result = effectTypesReducer(initialState, action);
    expect(result).toEqual(finalState);
  });

  it('checknig effect type twice should not change the state', () => {
    let initialState = ['Nonsense'];
    let finalState = ['Nonsense'];
    let action = { type: EFFECT_TYPE_CHECK, payload: 'Nonsense' };

    let result = effectTypesReducer(initialState, action);
    expect(result).toEqual(finalState);
  });


  it('checking different effect type should add it', () => {
    let initialState = ['Nonsense'];
    let finalState = ['Nonsense', 'Missense'];
    let action = { type: EFFECT_TYPE_CHECK, payload: 'Missense' };

    let result = effectTypesReducer(initialState, action);
    expect(result).toEqual(finalState);
  });

  it('unchecknig effect type should remove it', () => {
    let initialState = ['Nonsense'];
    let finalState = [];
    let action = { type: EFFECT_TYPE_UNCHECK, payload: 'Nonsense' };

    let result = effectTypesReducer(initialState, action);
    expect(result).toEqual(finalState);
  });

  it('unchecknig effect type twice should not change state', () => {
    let initialState = [];
    let finalState = [];
    let action = { type: EFFECT_TYPE_UNCHECK, payload: 'Nonsense' };

    let result = effectTypesReducer(initialState, action);
    expect(result).toEqual(finalState);
  });

});
