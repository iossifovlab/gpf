import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoToolResultsChartPerEffectComponent } from './pheno-tool-results-chart-per-effect.component';

describe('PhenoToolResultsChartPerEffectComponent', () => {
  let component: PhenoToolResultsChartPerEffectComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartPerEffectComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoToolResultsChartPerEffectComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolResultsChartPerEffectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
