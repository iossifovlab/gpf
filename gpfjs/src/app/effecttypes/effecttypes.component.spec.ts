/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement, NO_ERRORS_SCHEMA } from '@angular/core';

import { EffecttypesComponent } from './effecttypes.component';
import { EffecttypesColumnComponent } from './effecttypes-column.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { of } from 'rxjs';
import { ALL, CODING, LGDS, NONSYNONYMOUS, UTRS } from './effecttypes';

describe('EffecttypesComponent', () => {
  let component: EffecttypesComponent;
  let fixture: ComponentFixture<EffecttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        EffecttypesComponent,
        EffecttypesColumnComponent,
      ],
      providers: [
        StateRestoreService
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EffecttypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    component.effectTypes.selected = undefined;
    const selectInitialValuesSpy = spyOn(component, 'selectInitialValues').and.callThrough();
    const getStateSpy = spyOn(component['stateRestoreService'], 'getState');
    const selectEffectTypesSetSpy = spyOn(component, 'selectEffectTypesSet').and.callThrough();

    getStateSpy.and.returnValue(of({effectTypes: undefined}));
    component.ngOnInit();
    expect(selectInitialValuesSpy).toHaveBeenCalledTimes(1);
    expect(getStateSpy).toHaveBeenCalledTimes(1);
    expect(selectEffectTypesSetSpy.calls.allArgs()).toEqual([
      [['Nonsense', 'Frame-shift', 'Splice-site', 'No-frame-shift-newStop' ]],
    ]);
    expect(component.effectTypes.selected).toEqual([
      'Nonsense',
      'Frame-shift',
      'Splice-site',
      'No-frame-shift-newStop'
    ]);

    getStateSpy.and.returnValue(of({effectTypes: ['fakeEffectType']}));
    component.ngOnInit();
    expect(selectInitialValuesSpy).toHaveBeenCalledTimes(2);
    expect(getStateSpy).toHaveBeenCalledTimes(2);
    expect(selectEffectTypesSetSpy.calls.allArgs()).toEqual([
      [['Nonsense', 'Frame-shift', 'Splice-site', 'No-frame-shift-newStop']],
      [['Nonsense', 'Frame-shift', 'Splice-site', 'No-frame-shift-newStop']],
      [['fakeEffectType']]
    ]);
    expect(component.effectTypes.selected).toEqual([
      'fakeEffectType'
    ]);
  });

  it('should initialize button groups', () => {
    component.effectTypesButtons = undefined;
    component['initButtonGroups']();
    const expectedMap = new Map();
    expectedMap
      .set('ALL', ALL)
      .set('NONE', [])
      .set('LGDS', LGDS)
      .set('CODING', CODING)
      .set('NONSYNONYMOUS', NONSYNONYMOUS)
      .set('UTRS', UTRS);
    expect(component.effectTypesButtons).toEqual(expectedMap);
  });

  it('should effect type change', () => {
    component.effectTypes.selected = [];
    component.onEffectTypeChange({checked: true, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toEqual(['effectType1']);

    component.onEffectTypeChange({checked: true, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual(['effectType1', 'effectType2']);

    component.onEffectTypeChange({checked: false, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toEqual(['effectType2']);

    component.onEffectTypeChange({checked: false, effectType: 'effectType1'});
    expect(component.effectTypes.selected).toEqual(['effectType2']);

    component.onEffectTypeChange({checked: true, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual(['effectType2']);

    component.onEffectTypeChange({checked: false, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual([]);

    component.onEffectTypeChange({checked: false, effectType: 'effectType2'});
    expect(component.effectTypes.selected).toEqual([]);
  });

  it('should get state', () => {
    component.effectTypes = {selected: ['fakeEffectType1', 'fakeEffectType2']};
    component.getState().take(1).subscribe(state => expect(state).toEqual(
      {effectTypes: [ 'fakeEffectType1', 'fakeEffectType2' ]}
    ));
  });
});
