/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { GenotypeBlockComponent } from './genotype-block.component';
import { GenderComponent } from '../gender/gender.component';
import { VarianttypesComponent } from '../varianttypes/varianttypes.component';
import { EffecttypesComponent } from '../effecttypes/effecttypes.component';
import { PedigreeSelectorComponent } from '../pedigree-selector/pedigree-selector.component';

import { Dataset } from '../dataset/dataset';
import { DatasetService } from '../dataset/dataset.service';
import { DatasetServiceStub } from '../dataset/dataset.service.spec';

let datasetService = new DatasetServiceStub(undefined, undefined);


describe('GenotypeBlockComponent', () => {
  let component: GenotypeBlockComponent;
  let fixture: ComponentFixture<GenotypeBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenderComponent,
        VarianttypesComponent,
        EffecttypesComponent,
        GenotypeBlockComponent,
        PedigreeSelectorComponent,
      ],
      imports: [
        NgbModule.forRoot(),
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
    fixture = TestBed.createComponent(GenotypeBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
