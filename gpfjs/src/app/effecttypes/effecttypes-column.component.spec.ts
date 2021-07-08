/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement, NO_ERRORS_SCHEMA } from '@angular/core';

import { EffecttypesColumnComponent } from './effecttypes-column.component';
import { of } from 'rxjs';
import { ALL, CODING, LGDS, NONSYNONYMOUS, UTRS } from './effecttypes';

describe('EffecttypesColumnComponent', () => {
  let component: EffecttypesColumnComponent;
  let fixture: ComponentFixture<EffecttypesColumnComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        EffecttypesColumnComponent,
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EffecttypesColumnComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should check effect type', () => {
    const emitSpy = spyOn(component.effectTypeEvent, 'emit');
    component.effectTypesLabels = ['label1', 'label2', 'label3'];

    component.checkEffectType(-1, true);
    component.checkEffectType(-1, false);
    component.checkEffectType(4, true);
    component.checkEffectType(4, false);
    expect(emitSpy).not.toHaveBeenCalled();

    component.checkEffectType(0, true);
    component.checkEffectType(0, false);
    component.checkEffectType(1, true);
    component.checkEffectType(1, false);
    component.checkEffectType(2, true);
    component.checkEffectType(2, false);
    expect(emitSpy.calls.allArgs()).toEqual([
      [{ effectType: 'label1', checked: true }],
      [{ effectType: 'label1', checked: false }],
      [{ effectType: 'label2', checked: true }],
      [{ effectType: 'label2', checked: false }],
      [{ effectType: 'label3', checked: true }],
      [{ effectType: 'label3', checked: false }],
    ]);
  });
});
