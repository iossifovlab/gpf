import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PhenoToolResultsChartComponent } from './pheno-tool-results-chart.component';

describe('PhenoToolResultsChartComponent', () => {
  let component: PhenoToolResultsChartComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoToolResultsChartComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolResultsChartComponent);
    component = fixture.componentInstance;
    component.phenoToolResults = {
      description: undefined,
      results: []
    };

    Object.defineProperty(URL, 'createObjectURL', {
      value: jest.fn()
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      value: jest.fn()
    });

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
