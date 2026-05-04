import { AfterViewInit, Component, Input, OnChanges, OnInit, ViewChild } from '@angular/core';
import { PhenoToolResults, PhenoToolResult } from '../pheno-tool/pheno-tool-results';
import * as d3 from 'd3';

@Component({
  selector: 'gpf-pheno-tool-results-chart',
  templateUrl: './pheno-tool-results-chart.component.html',
  styleUrls: ['./pheno-tool-results-chart.component.css'],
  standalone: false
})
export class PhenoToolResultsChartComponent implements OnInit, OnChanges, AfterViewInit {
  @ViewChild('innerGroup', {static: true}) public innerGroup: any;
  @Input() public phenoToolResults: PhenoToolResults;
  @Input() public width = 1060;
  @Input() public height = 700;
  public columnCount: number;
  @Input() public innerHeight = 450;
  public yScale: d3.ScaleLinear<number, number>;

  public ngOnInit(): void {
    this.columnCount = this.phenoToolResults.results.length;
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

  public ngAfterViewInit(): void {
    this.createImgFromSvg();
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

  public getViewBox(): string {
    return `0 0 ${this.columnCount > 4 ? this.columnCount * 260 : this.width} ${this.height}`;
  }

  private createImgFromSvg(): void {
    const container = document.getElementById('image-download-container');
    const svg: SVGSVGElement = document.querySelector('#pheno-tool-result');

    if (container && svg) {
      svg.style.backgroundColor = 'white';
      svg.style.font = '16px Roboto, sans-serif, "Noto Sans Symbols 2", "Noto Sans Math"';

      const svgStr = new XMLSerializer().serializeToString(svg);

      const img = new Image();
      img.addEventListener('load', () => {
        const bbox = svg.getBBox();
        const width = bbox.width < 1000 ? 1000 : bbox.width;
        const height = bbox.height;

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        const context = canvas.getContext('2d');
        context.drawImage(img, 0, 0, width, height);

        const a = document.getElementById('image-download') as HTMLAnchorElement;
        a.download = 'pheno-tool-report.png';
        a.href = canvas.toDataURL();
      });
      img.src = 'data:image/svg+xml;base64,'+ window.btoa(unescape(encodeURIComponent(svgStr)));
    }
  }
}
