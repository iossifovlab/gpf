import { Component, OnInit, Input } from '@angular/core';
import { PhenoToolResults, PhenoToolResult } from '../pheno-tool/pheno-tool-results';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-pheno-tool-results-chart',
  templateUrl: './pheno-tool-results-chart.component.html',
  styleUrls: ['./pheno-tool-results-chart.component.css']
})
export class PhenoToolResultsChartComponent implements OnInit {
  @Input() phenoToolResults: PhenoToolResults;
  @Input() width = 450;
  @Input() height = 1060;
  yScale: d3.ScaleLinear<number, number>;

  constructor() { }

  ngOnInit() {
    this.yScale = d3.scaleLinear().range([this.height, 0]);
    this.calcMinMax();
  }

  addRange(phenoToolResult: PhenoToolResult, outputValues: Array<number>) {
    outputValues.push(phenoToolResult.mean + phenoToolResult.deviation);
    outputValues.push(phenoToolResult.mean - phenoToolResult.deviation);
  }

  calcMinMax() {
    let values = new Array<number>() ;

    for (let result of this.phenoToolResults.results) {
      this.addRange(result.maleResult.positive, values);
      this.addRange(result.maleResult.negative, values);
      this.addRange(result.femaleResult.positive, values);
      this.addRange(result.femaleResult.negative, values);
    }

    let min = Math.min( ...values );
    let max = Math.max( ...values );

    this.yScale.domain([min, max]);
  }

}
