import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PhenoToolResultsChartComponent } from './pheno-tool-results-chart.component';

describe('PhenoToolResultsChartComponent', () => {
  let component: PhenoToolResultsChartComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoToolResultsChartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolResultsChartComponent);
    component = fixture.componentInstance;
    component.phenoToolResults = {
      'fromJson': jest.fn()
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
