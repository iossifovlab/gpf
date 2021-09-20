import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Injectable } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { HistogramData } from 'app/measures/measures';
import { MeasuresService } from 'app/measures/measures.service';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { of } from 'rxjs/internal/observable/of';

import { ContinuousFilterComponent } from './continuous-filter.component';

export class MeasuresServiceMock {

  public getContinuousMeasures(
    datasetId: string
  ) {

  }

  public getMeasureHistogram(
    datasetId: string,
    measureName: string
  ): Observable<HistogramData> {
    return of({datasetId: datasetId, measureName: measureName}  as any);
  }

  public getMeasurePartitions(
    datasetId: string,
    measureName: string,
    rangeStart: number,
    rangeEnd: number
  ) {

  }

  public getRegressions(datasetId: string) {

  }
}

describe('ContinuousFilterComponent', () => {
  let component: ContinuousFilterComponent;
  let fixture: ComponentFixture<ContinuousFilterComponent>;
  const measuresServiceMock = new MeasuresServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ContinuousFilterComponent],
      providers: [{provide: MeasuresService, useValue: measuresServiceMock}, ConfigService],
      imports: [HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContinuousFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  /*it('should set histogram data on changes', () => {
    component.histogramData = undefined;
    component.datasetId = undefined;
    component.measureName = undefined;

    component.ngOnChanges(undefined);

    expect(component.histogramData).toEqual(undefined);

    component.datasetId = 'datasetId';
    component.measureName = undefined;

    component.ngOnChanges(undefined);

    expect(component.histogramData).toEqual(undefined);

    component.datasetId = undefined;
    component.measureName = 'measureName';

    component.ngOnChanges(undefined);

    expect(component.histogramData).toEqual(undefined);

    component.datasetId = 'datasetId';
    component.measureName = 'measureName';

    component.ngOnChanges(undefined);

    expect(component.histogramData).toEqual({datasetId: 'datasetId', measureName: 'measureName'}  as any);
  });*/
});
