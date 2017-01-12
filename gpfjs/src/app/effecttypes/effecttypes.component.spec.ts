/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { EffecttypesComponent } from './effecttypes.component';

describe('EffecttypesComponent', () => {
  let component: EffecttypesComponent;
  let fixture: ComponentFixture<EffecttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [EffecttypesComponent],
      imports: [
      ],

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
});
