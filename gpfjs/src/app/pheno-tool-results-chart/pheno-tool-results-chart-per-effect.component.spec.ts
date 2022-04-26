import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PhenoToolEffectTypesComponent } from 'app/pheno-tool-effect-types/pheno-tool-effect-types.component';
import { PresentInParentComponent } from 'app/present-in-parent/present-in-parent.component';
import { NumberWithExpPipe } from 'app/utils/number-with-exp.pipe';
import * as d3 from 'd3';

import { PhenoToolResultsChartPerEffectComponent } from './pheno-tool-results-chart-per-effect.component';

class PhenoToolResultMock {
  public count;
  public deviation;
  public mean;
}

const phenoToolResultsPerGenderMock = {
  positive: PhenoToolResultMock,
  negative: PhenoToolResultMock,
  pvalue: 0,
};

const phenoToolResultsPerEffectMock = {
  effect: '',
  maleResult: phenoToolResultsPerGenderMock,
  femaleResult: phenoToolResultsPerGenderMock,
};

describe('PhenoToolResultsChartPerEffectComponent', () => {
  let component: PhenoToolResultsChartPerEffectComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartPerEffectComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolResultsChartPerEffectComponent,
        PresentInParentComponent,
        PhenoToolEffectTypesComponent,
        NumberWithExpPipe,
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolResultsChartPerEffectComponent);
    component = fixture.componentInstance;
    component.effectResults = phenoToolResultsPerEffectMock as any;
    component.yScale = d3.scaleLinear<number, number>();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
