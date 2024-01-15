import { Component, Input, OnChanges, OnInit, ViewChild } from '@angular/core';
import { PhenoToolResults, PhenoToolResult } from '../pheno-tool/pheno-tool-results';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-pheno-tool-results-chart',
  templateUrl: './pheno-tool-results-chart.component.html',
  styleUrls: ['./pheno-tool-results-chart.component.css']
})
export class PhenoToolResultsChartComponent implements OnInit, OnChanges {
  @ViewChild('innerGroup', {static: true}) public innerGroup: any;
  @Input() public phenoToolResults: PhenoToolResults;
  @Input() public width = 1060;
  @Input() public height = 700;
  @Input() public innerHeight = 450;
  public yScale: d3.ScaleLinear<number, number>;

  public ngOnInit(): void {
    this.width = this.phenoToolResults.results.length;
  }

  public ngOnChanges(): void {
    this.yScale = d3.scaleLinear().range([this.innerHeight, 0]);
    this.calcMinMax();
    const svg = d3.select(this.innerGroup.nativeElement);
    svg.selectAll('.axis').remove();
    svg.append('g')
      .attr('class', 'axis')
      .call(d3.axisLeft(this.yScale))
      .attr('transform', 'translate(42,0)');
  }

  public addRange(phenoToolResult: PhenoToolResult, outputValues: Array<number>): void {
    outputValues.push(phenoToolResult.mean + phenoToolResult.deviation);
    outputValues.push(phenoToolResult.mean - phenoToolResult.deviation);
  }

  public calcMinMax(): void {
    const values = new Array<number>();

    for (const result of this.phenoToolResults.results) {
      this.addRange(result.maleResult.positive, values);
      this.addRange(result.maleResult.negative, values);
      this.addRange(result.femaleResult.positive, values);
      this.addRange(result.femaleResult.negative, values);
    }

    const min = Math.min(...values);
    const max = Math.max(...values);

    this.yScale.domain([min, max]);
  }

  public calculateGap(): number {
    if (!this.phenoToolResults.results ||
        !this.phenoToolResults.results.length) {
      return 0;
    }
    return (this.width - 200) / this.phenoToolResults.results.length;
  }
}
