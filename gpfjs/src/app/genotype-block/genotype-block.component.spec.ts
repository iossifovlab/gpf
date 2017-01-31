/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { GenotypeBlockComponent } from './genotype-block.component';

describe('GenotypeBlockComponent', () => {
  let component: GenotypeBlockComponent;
  let fixture: ComponentFixture<GenotypeBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GenotypeBlockComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypeBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
