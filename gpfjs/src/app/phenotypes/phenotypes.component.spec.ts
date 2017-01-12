/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';
import { Http } from '@angular/http';

import { PhenotypesComponent } from './phenotypes.component';
import { DatasetService } from '../dataset/dataset.service';
import { IdDescription } from '../common/iddescription';
import { Phenotype } from '../phenotypes/phenotype';
import { Dataset } from '../dataset/dataset';
import { DatasetServiceStub } from '../dataset/dataset.service.spec';

let datasetService = new DatasetServiceStub(undefined, undefined);


describe('PhenotypesComponent', () => {
  let component: PhenotypesComponent;
  let fixture: ComponentFixture<PhenotypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PhenotypesComponent],
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
    fixture = TestBed.createComponent(PhenotypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have undefined phenotypes before OnInit', () => {
    expect(component.phenotypes).toBe(undefined);
  });

  it('should have 2 phenotypes after OnInit', async(() => {
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      fixture.detectChanges();
      expect(component.phenotypes).toBeTruthy();
      expect(component.phenotypes.length).toBe(2);
      expect(component.phenotypes[0].id).toBe('autism');
      expect(component.phenotypes[1].id).toBe('unaffected');
    });

  }));

  it('should have all 2 phenotypes selected after OnInit', async(() => {
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      fixture.detectChanges();
      let selectedPhenotypes = component.getSelectedPhenotypes();
      expect(selectedPhenotypes).toEqual(new Set(['autism', 'unaffected']));
    });

  }));

  it('should have no phenotypes selected after OnInit', async(() => {
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      component.selectNone();
      fixture.detectChanges();
      let selectedPhenotypes = component.getSelectedPhenotypes();
      expect(selectedPhenotypes).toEqual(new Set([]));
    });

  }));

  it('should not throw error if selectNone is called before OnInit', () => {
    component.selectNone();
  });

  it('should not throw error if selectAll is called before OnInit', () => {
    component.selectAll();
  });

  it('should not throw error if getSelectedPhenotypes is called before OnInit', () => {
    component.getSelectedPhenotypes();
  });

});
