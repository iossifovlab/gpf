import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PhenoToolResultsChartPerResultComponent } from './pheno-tool-results-chart-per-result.component';

describe('PhenoToolResultsChartPerResultComponent', () => {
  let component: PhenoToolResultsChartPerResultComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartPerResultComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoToolResultsChartPerResultComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolResultsChartPerResultComponent);
    component = fixture.componentInstance;
    component.results = {
      rangeStart: undefined,
      rangeEnd: undefined,
      count: undefined,
      deviation: undefined,
      mean: undefined,
    };
    component.yScale = jest.fn() as any;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
