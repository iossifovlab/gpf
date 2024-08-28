import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { EffectTypesComponent } from './effect-types.component';
import { EffecttypesColumnComponent } from './effect-types-column.component';
import { ALL, CODING, LGDS, NONSYNONYMOUS, UTRS } from './effect-types';
import { of } from 'rxjs';
import { addEffectType, effectTypesReducer, removeEffectType, setEffectTypes } from './effect-types.state';
import { Store, StoreModule } from '@ngrx/store';

describe('EffectTypesComponent', () => {
  let component: EffectTypesComponent;
  let fixture: ComponentFixture<EffectTypesComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        EffectTypesComponent,
        EffecttypesColumnComponent,
      ],
      imports: [StoreModule.forRoot({effectTypes: effectTypesReducer})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(EffectTypesComponent);
    component = fixture.componentInstance;

    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2', 'value3']));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    const onEffectTypeChangeSpy = jest.spyOn(component, 'onEffectTypeChange');
    const selectInitialValuesSpy = jest.spyOn(component, 'selectInitialValues');

    component.ngOnInit();
    expect(onEffectTypeChangeSpy.mock.calls).toEqual([
      [{ checked: true, effectType: 'value1' }],
      [{ checked: true, effectType: 'value2' }],
      [{ checked: true, effectType: 'value3' }]
    ]);
    expect(selectInitialValuesSpy).not.toHaveBeenCalled();

    jest.spyOn(store, 'select').mockReturnValue(of([]));
    jest.spyOn(store, 'dispatch').mockReturnValue(null);

    component.ngOnInit();
    expect(onEffectTypeChangeSpy).toHaveBeenCalledTimes(3);
    expect(selectInitialValuesSpy).toHaveBeenCalledTimes(1);
  });

  it('should initialize button groups', () => {
    component.effectTypesButtons = undefined;
    component['initButtonGroups']();
    const expectedMap = new Map();
    expectedMap
      .set('ALL', ALL)
      .set('NONE', new Set())
      .set('LGDS', LGDS)
      .set('CODING', CODING)
      .set('NONSYNONYMOUS', NONSYNONYMOUS)
      .set('UTRS', UTRS);
    expect(component.effectTypesButtons).toEqual(expectedMap);
  });

  it('should update variant types', () => {
    component.effectTypes.selected = undefined;
    component['store'] = { dispatch: () => null } as never;
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.setEffectTypes(mockSet);

    expect(component.effectTypes.selected).toStrictEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, setEffectTypes({ effectTypes: [...mockSet]}));
  });

  it('should effect type change', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.effectTypes.selected = new Set();

    component.onEffectTypeChange({checked: true, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toStrictEqual(new Set(['effectType1']));

    component.onEffectTypeChange({checked: true, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toStrictEqual(new Set(['effectType1', 'effectType2']));

    component.onEffectTypeChange({checked: false, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toStrictEqual(new Set(['effectType2']));

    component.onEffectTypeChange({checked: false, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toStrictEqual(new Set(['effectType2']));

    component.onEffectTypeChange({checked: true, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toStrictEqual(new Set(['effectType2']));

    component.onEffectTypeChange({checked: false, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toStrictEqual(new Set([]));

    component.onEffectTypeChange({checked: false, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toStrictEqual(new Set([]));

    expect(dispatchSpy.mock.calls).toEqual([
      [addEffectType({effectType: 'effectType1'})],
      [addEffectType({effectType: 'effectType2'})],
      [removeEffectType({effectType: 'effectType1'})],
      [removeEffectType({effectType: 'effectType2'})],
    ]);
  });

  it('should not modify original effect group values', () => {
    const initial = new Set(['testEffect']);
    component.setEffectTypes(initial);
    component.onEffectTypeChange({effectType: 'newTestEffect', checked: true});
    // component has properly selected new effect
    expect(component.effectTypes.selected).toStrictEqual(new Set(['testEffect', 'newTestEffect']));
    // but the original set is not modified
    expect(initial).toStrictEqual(new Set(['testEffect']));
  });
});
