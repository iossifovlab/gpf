import { Component, Input } from '@angular/core';
import { PhenoToolResult } from '../pheno-tool/pheno-tool-results';

@Component({
  selector: '[gpf-pheno-tool-results-chart-per-result]',
  templateUrl: './pheno-tool-results-chart-per-result.component.html',
  standalone: false
})
export class PhenoToolResultsChartPerResultComponent {
  @Input() public results: PhenoToolResult;
  @Input() public yScale: d3.ScaleLinear<number, number>;
  @Input() public color: string;
  @Input() public fillColor: string;

  public get startY(): number {
    return this.yScale(this.results.rangeStart);
  }

  public get endY(): number {
    return this.yScale(this.results.rangeEnd);
  }

  public get centerY(): number {
    return (this.endY + this.startY) / 2;
  }
}
