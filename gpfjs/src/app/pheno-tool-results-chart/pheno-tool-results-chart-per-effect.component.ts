import { Component, Input } from '@angular/core';
import { PhenoToolResultsPerEffect } from '../pheno-tool/pheno-tool-results';

@Component({
    selector: '[gpf-pheno-tool-results-chart-per-effect]',
    templateUrl: './pheno-tool-results-chart-per-effect.component.html',
    standalone: false
})
export class PhenoToolResultsChartPerEffectComponent {
  @Input() public effectResults: PhenoToolResultsPerEffect;
  @Input() public yScale: d3.ScaleLinear<number, number>;

  public get maleEndY(): number {
    const endNegative = this.effectResults.maleResult.negative.rangeStart;
    const endPositive = this.effectResults.maleResult.positive.rangeStart;
    return this.yScale(Math.min(endNegative, endPositive)) + 20;
  }

  public get femaleEndY(): number {
    const endNegative = this.effectResults.femaleResult.negative.rangeStart;
    const endPositive = this.effectResults.femaleResult.positive.rangeStart;
    return this.yScale(Math.min(endNegative, endPositive)) + 20;
  }
}
