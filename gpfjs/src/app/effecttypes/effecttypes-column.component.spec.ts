/* tslint:disable:no-unused-variable */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { EffecttypesColumnComponent } from './effecttypes-column.component';

describe('EffecttypesColumnComponent', () => {
  let component: EffecttypesColumnComponent;
  let fixture: ComponentFixture<EffecttypesColumnComponent>;

  beforeEach(waitForAsync(() => {
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
    component.effectTypesLabels = new Set(['label1', 'label2', 'label3']);

    component.checkEffectType('label0', true);
    component.checkEffectType('label0', false);
    component.checkEffectType('label4', true);
    component.checkEffectType('label4', false);
    expect(emitSpy).not.toHaveBeenCalled();

    component.checkEffectType('label1', true);
    component.checkEffectType('label1', false);
    component.checkEffectType('label2', true);
    component.checkEffectType('label2', false);
    component.checkEffectType('label3', true);
    component.checkEffectType('label3', false);
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
