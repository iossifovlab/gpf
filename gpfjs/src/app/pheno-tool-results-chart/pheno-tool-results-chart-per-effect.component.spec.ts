import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { PhenoToolEffectTypesComponent } from 'app/pheno-tool-effect-types/pheno-tool-effect-types.component';
import { PhenoToolResultsPerEffect } from 'app/pheno-tool/pheno-tool-results';
import { PresentInParentComponent } from 'app/present-in-parent/present-in-parent.component';
import { NumberWithExpPipe } from 'app/utils/number-with-exp.pipe';
import * as d3 from 'd3';

import { PhenoToolResultsChartPerEffectComponent } from './pheno-tool-results-chart-per-effect.component';

class PhenoToolResultMock {
  count;
  deviation;
  mean;
}

const PhenoToolResultsPerGenderMock: any = {
  positive: PhenoToolResultMock,
  negative: PhenoToolResultMock,
  pvalue: 0,
};

const PhenoToolResultsPerEffectMock: any = {
  effect: '',
  maleResult: PhenoToolResultsPerGenderMock,
  femaleResult: PhenoToolResultsPerGenderMock,
};

function ScaleLinearMock() { return 0; }

describe('PhenoToolResultsChartPerEffectComponent', () => {
  let component: PhenoToolResultsChartPerEffectComponent;
  let fixture: ComponentFixture<PhenoToolResultsChartPerEffectComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolResultsChartPerEffectComponent,
        PresentInParentComponent,
        PhenoToolEffectTypesComponent,
        NumberWithExpPipe,
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolResultsChartPerEffectComponent);
    component = fixture.componentInstance;
    component.effectResults = PhenoToolResultsPerEffectMock;
    component.yScale = d3.scaleLinear<number, number>();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
