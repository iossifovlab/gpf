/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { GenderComponent } from './gender.component';

import { gpfReducer } from '../store/gpf-store';

describe('GenderComponent', () => {
  let component: GenderComponent;
  let fixture: ComponentFixture<GenderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GenderComponent],
      imports: [

      ],

    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('both genders should be selected after create', () => {
    expect(component.male).toBeTruthy();
    expect(component.female).toBeTruthy();
  });

  it('both genders should be selected after selectAll', () => {
    component.selectAll();

    expect(component.male).toBeTruthy();
    expect(component.female).toBeTruthy();
  });

  it('both genders should be un-selected after selectNone', () => {
    component.selectNone();

    expect(component.male).toBe(false);
    expect(component.female).toBe(false);
  });

});
