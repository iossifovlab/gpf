/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { StudytypesComponent } from './studytypes.component';
import { Dataset } from '../dataset/dataset';
import { DatasetServiceStub } from '../dataset/dataset.service.spec';
import { DatasetService } from '../dataset/dataset.service';
import { IdDescription } from '../common/iddescription';

let datasetService = new DatasetServiceStub(undefined, undefined);
describe('StudytypesComponent', () => {
  let component: StudytypesComponent;
  let fixture: ComponentFixture<StudytypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [StudytypesComponent],
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
    fixture = TestBed.createComponent(StudytypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
