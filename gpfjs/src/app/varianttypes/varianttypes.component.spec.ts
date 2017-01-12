/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { VarianttypesComponent } from './varianttypes.component';

describe('VarianttypesComponent', () => {
  let component: VarianttypesComponent;
  let fixture: ComponentFixture<VarianttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [VarianttypesComponent],
      imports: [
      ],

    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VarianttypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
