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
    let endNegative = this.effectResults.maleResult.negative.rangeStart;
    let endPositive = this.effectResults.maleResult.positive.rangeStart;
    return this.yScale(Math.min(endNegative, endPositive)) + 20;
  }

  get femaleEndY() {
    let endNegative = this.effectResults.femaleResult.negative.rangeStart;
    let endPositive = this.effectResults.femaleResult.positive.rangeStart;
    return this.yScale(Math.min(endNegative, endPositive)) + 20;
  }

}
