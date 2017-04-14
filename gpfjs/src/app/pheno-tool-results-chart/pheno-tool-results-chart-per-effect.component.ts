import { Component, OnInit, Input } from '@angular/core';
import { PhenoToolResultsPerEffect } from '../pheno-tool/pheno-tool-results';

@Component({
  selector: '[gpf-pheno-tool-results-chart-per-effect]',
  templateUrl: './pheno-tool-results-chart-per-effect.component.html',
})
export class PhenoToolResultsChartPerEffectComponent implements OnInit {
  @Input() effectResults: PhenoToolResultsPerEffect
  @Input() yScale: d3.ScaleLinear<number, number>;

  constructor() { }

  ngOnInit() {

  }

  get maleEndY() {
    let endNegative = this.effectResults.maleResult.negative.mean -
                      this.effectResults.maleResult.negative.deviation;

    let endPositive = this.effectResults.maleResult.positive.mean -
                      this.effectResults.maleResult.positive.deviation;
    return this.yScale(Math.min(endNegative, endPositive)) + 20;
  }

  get femaleEndY() {
    let endNegative = this.effectResults.femaleResult.negative.mean -
                      this.effectResults.femaleResult.negative.deviation;

    let endPositive = this.effectResults.femaleResult.positive.mean -
                      this.effectResults.femaleResult.positive.deviation;
    return this.yScale(Math.min(endNegative, endPositive)) + 20;
  }

}
