/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { StudyTypesComponent } from './study-types.component';

describe('StudyTypesComponent', () => {
  let component: StudyTypesComponent;
  let fixture: ComponentFixture<StudyTypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ StudyTypesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyTypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
