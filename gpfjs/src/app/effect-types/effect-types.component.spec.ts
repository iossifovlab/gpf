import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { EffectTypesComponent } from './effect-types.component';
import { EffecttypesColumnComponent } from './effect-types-column.component';
import { ALL, CODING, LGDS, NONSYNONYMOUS, UTRS } from './effect-types';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';
import { AddEffectType, RemoveEffectType, SetEffectTypes, EffecttypesState } from './effect-types.state';

describe('EffectTypesComponent', () => {
  let component: EffectTypesComponent;
  let fixture: ComponentFixture<EffectTypesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        EffectTypesComponent,
        EffecttypesColumnComponent,
      ],
      imports: [NgxsModule.forRoot([EffecttypesState], {developmentMode: true})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(EffectTypesComponent);
    component = fixture.componentInstance;

    component['store'] = {
      selectOnce: () => of({effectTypes: ['value1', 'value2', 'value3']}),
      dispatch: () => null
    } as never;

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

    component['store'] = {
      selectOnce: () => of({effectTypes: []}),
      dispatch: () => null
    } as never;

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
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, new SetEffectTypes(mockSet));
  });

  it('should effect type change', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
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
      [new AddEffectType('effectType1')],
      [new AddEffectType('effectType2')],
      [new RemoveEffectType('effectType1')],
      [new RemoveEffectType('effectType2')]
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
