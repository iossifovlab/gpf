import { Component, OnInit, Input, ViewChild, SimpleChanges } from '@angular/core';
import { PhenoToolResults, PhenoToolResult } from '../pheno-tool/pheno-tool-results';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-pheno-tool-results-chart',
  templateUrl: './pheno-tool-results-chart.component.html',
  styleUrls: ['./pheno-tool-results-chart.component.css']
})
export class PhenoToolResultsChartComponent implements OnInit {
  @ViewChild('innerGroup') innerGroup: any;
  @Input() phenoToolResults: PhenoToolResults;
  @Input() width = 1060;
  @Input() height = 700;
  @Input() innerHeight = 450;
  yScale: d3.ScaleLinear<number, number>;


  constructor() { }

  ngOnInit() {

  }

  ngOnChanges(changes: SimpleChanges) {
    this.yScale = d3.scaleLinear().range([this.innerHeight, 0]);
    this.calcMinMax();

    let svg = d3.select(this.innerGroup.nativeElement);
    svg.selectAll(".axis").remove();
    svg.append("g")
      .attr("class", "axis")
      .call(d3.axisLeft(this.yScale));
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

  calculateGap() {
    if (!this.phenoToolResults.results ||
        !this.phenoToolResults.results.length) {
      return 0;
    }
    return (this.width - 200) / this.phenoToolResults.results.length;
  }

}
