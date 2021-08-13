import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { PhenoToolResultsChartPerResultComponent } from './pheno-tool-results-chart-per-result.component';

describe('PhenoToolResultsChartPerResultComponent', () => {
  let component: PhenoToolResultsChartPerResultComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartPerResultComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoToolResultsChartPerResultComponent]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolResultsChartPerResultComponent);
    component = fixture.componentInstance;
    component.results = jasmine.createSpyObj('PhenoToolResult', ['rangeStart', 'rangeEnd']);
    component.yScale = jasmine.createSpy() as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
