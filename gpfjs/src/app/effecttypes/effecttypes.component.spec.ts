/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { EffecttypesComponent } from './effecttypes.component';

import { DatasetService } from '../dataset/dataset.service';
import { DatasetServiceStub } from '../dataset/dataset.service.spec';


let datasetService = new DatasetServiceStub(undefined, undefined);


describe('EffecttypesComponent', () => {
  let component: EffecttypesComponent;
  let fixture: ComponentFixture<EffecttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [EffecttypesComponent],
      imports: [
      ],
      providers: [
        {
          provide: DatasetService,
          useValue: datasetService
        }
      ]
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
