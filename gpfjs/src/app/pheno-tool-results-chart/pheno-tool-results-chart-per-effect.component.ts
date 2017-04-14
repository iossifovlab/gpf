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

}
