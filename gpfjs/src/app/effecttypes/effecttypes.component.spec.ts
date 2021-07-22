/* tslint:disable:no-unused-variable */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { EffecttypesComponent } from './effecttypes.component';
import { EffecttypesColumnComponent } from './effecttypes-column.component';
import { ALL, CODING, LGDS, NONSYNONYMOUS, UTRS } from './effecttypes';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';
import { AddEffectType, RemoveEffectType, SetEffectTypes, EffecttypesState } from './effecttypes.state';

describe('EffecttypesComponent', () => {
  let component: EffecttypesComponent;
  let fixture: ComponentFixture<EffecttypesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        EffecttypesComponent,
        EffecttypesColumnComponent,
      ],
      imports: [NgxsModule.forRoot([EffecttypesState])],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EffecttypesComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce(f) {
        return of({effectTypes: ['value1', 'value2', 'value3']});
      },
      dispatch(set) {}
    } as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    const onEffectTypeChangeSpy = spyOn(component, 'onEffectTypeChange');
    const selectInitialValuesSpy = spyOn(component, 'selectInitialValues');

    component.ngOnInit();
    expect(onEffectTypeChangeSpy.calls.allArgs()).toEqual([
      [{ checked: true, effectType: 'value1' }],
      [{ checked: true, effectType: 'value2' }],
      [{ checked: true, effectType: 'value3' }]
    ]);
    expect(selectInitialValuesSpy).not.toHaveBeenCalled();

    component['store'] = {
      selectOnce(f) {
        return of({effectTypes: []});
      },
      dispatch(set) {}
    } as any;
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
    component['store'] = { dispatch(set) {} } as any;
    const dispatchSpy = spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.setEffectTypes(mockSet);

    expect(component.effectTypes.selected).toEqual(mockSet);
    expect(dispatchSpy).toHaveBeenCalledOnceWith(new SetEffectTypes(mockSet));
  });

  it('should effect type change', () => {
    const dispatchSpy = spyOn(component['store'], 'dispatch');
    component.effectTypes.selected = new Set();

    component.onEffectTypeChange({checked: true, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toEqual(new Set(['effectType1']));

    component.onEffectTypeChange({checked: true, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual(new Set(['effectType1', 'effectType2']));

    component.onEffectTypeChange({checked: false, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toEqual(new Set(['effectType2']));

    component.onEffectTypeChange({checked: false, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toEqual(new Set(['effectType2']));

    component.onEffectTypeChange({checked: true, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual(new Set(['effectType2']));

    component.onEffectTypeChange({checked: false, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual(new Set([]));

    component.onEffectTypeChange({checked: false, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual(new Set([]));

    expect(dispatchSpy.calls.allArgs()).toEqual([
      [new AddEffectType('effectType1')],
      [new AddEffectType('effectType2')],
      [new RemoveEffectType('effectType1')],
      [new RemoveEffectType('effectType2')]
    ]);
  });
});
