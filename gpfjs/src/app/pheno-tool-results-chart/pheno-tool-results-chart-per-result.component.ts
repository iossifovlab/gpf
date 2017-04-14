import { Component, OnInit, Input } from '@angular/core';
import { PhenoToolResult } from '../pheno-tool/pheno-tool-results';

@Component({
  selector: '[gpf-pheno-tool-results-chart-per-result]',
  templateUrl: './pheno-tool-results-chart-per-result.component.html',
})
export class PhenoToolResultsChartPerResultComponent implements OnInit {
  @Input() results: PhenoToolResult
  @Input() yScale: d3.ScaleLinear<number, number>;
  @Input() color: string;
  @Input() fillColor: string;

  constructor() { }

  ngOnInit() {
  }

  get startY() {
    return this.yScale(this.results.rangeStart);
  }

  get endY() {
    return this.yScale(this.results.rangeEnd);
  }

  get centerY() {
    return (this.endY + this.startY)/2;
  }

}
