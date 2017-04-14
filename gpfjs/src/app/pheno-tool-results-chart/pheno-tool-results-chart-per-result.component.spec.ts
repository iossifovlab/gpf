import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoToolResultsChartPerResultComponent } from './pheno-tool-results-chart-per-result.component';

describe('PhenoToolResultsChartPerResultComponent', () => {
  let component: PhenoToolResultsChartPerResultComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartPerResultComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoToolResultsChartPerResultComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolResultsChartPerResultComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
