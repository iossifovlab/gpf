import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { HistogramData } from 'app/measures/measures';
import { MeasuresService } from 'app/measures/measures.service';
import { Observable, of } from 'rxjs';

import { ContinuousFilterComponent } from './continuous-filter.component';
import { StoreModule } from '@ngrx/store';

class MeasuresServiceMock {
  public getContinuousMeasures(): void {
    return null;
  }

  public getMeasureHistogram(datasetId: string, measureName: string): Observable<HistogramData> {
    return of({datasetId, measureName} as any);
  }

  public getMeasurePartitions(): void {
    return null;
  }

  public getRegressions(): void {
    return null;
  }
}

describe('ContinuousFilterComponent', () => {
  let component: ContinuousFilterComponent;
  let fixture: ComponentFixture<ContinuousFilterComponent>;
  const measuresServiceMock = new MeasuresServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ContinuousFilterComponent],
      providers: [{provide: MeasuresService, useValue: measuresServiceMock}, ConfigService],
      imports: [HttpClientTestingModule, StoreModule.forRoot()]
    })
      .compileComponents();

    fixture = TestBed.createComponent(ContinuousFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
