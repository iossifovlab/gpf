/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { RegionsBlockComponent } from './regions-block.component';

describe('RegionsBlockComponent', () => {
  let component: RegionsBlockComponent;
  let fixture: ComponentFixture<RegionsBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RegionsBlockComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegionsBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
