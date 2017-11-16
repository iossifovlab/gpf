/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { PedigreeSelectorComponent } from './pedigree-selector.component';

import { gpfReducer } from '../store/gpf-store';

describe('PedigreeselectorComponent', () => {
  let component: PedigreeSelectorComponent;
  let fixture: ComponentFixture<PedigreeSelectorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PedigreeSelectorComponent],
      imports: [

      ],
      providers: [
      ]

    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PedigreeSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
