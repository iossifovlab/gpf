import {
  Input,
  Component,
  ViewChild,
  ChangeDetectionStrategy,
  ElementRef,
  OnChanges
} from '@angular/core';
import { CategoricalHistogram } from 'app/gene-scores/gene-scores';

import * as d3 from 'd3';

@Component({
  selector: 'gpf-categorical-histogram',
  templateUrl: './categorical-histogram.component.html',
  styleUrl: './categorical-histogram.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CategoricalHistogramComponent implements OnChanges {
  @Input() public width: number;
  @Input() public height: number;
  @Input() public marginLeft = 100;
  @Input() public marginTop = 10;
  @ViewChild('histogramContainer', {static: true}) public histogramContainer: ElementRef;

  @Input() public showCounts = true;
  @Input() public showMinMaxInput: boolean;

  @Input() public histogram: CategoricalHistogram;

  private svg: d3.Selection<SVGElement, unknown, null, undefined>;

  @Input() public isInteractive = true;
  @Input() public singleScoreValue: number;

  public xScale: d3.ScaleBand<string>;
  public scaleXAxis: d3.ScaleThreshold<number, number, never>;
  public scaleYAxis: d3.ScaleLinear<number, number, never>
                     | d3.ScaleLogarithmic<number, number, never>;

  public ngOnChanges(): void {
    d3.select(this.histogramContainer.nativeElement).selectAll('g').remove();
    d3.select(this.histogramContainer.nativeElement).selectAll('rect').remove();
    this.redrawHistogram();
  }

  public singleScoreValueIsValid(): boolean {
    return this.singleScoreValue !== undefined && this.singleScoreValue !== null && !isNaN(this.singleScoreValue);
  }

  private redrawHistogram(): void {
    const width = 450.0;
    const height = 50;

    const svg = d3.select(
      this.histogramContainer.nativeElement
    ) as d3.Selection<SVGElement, unknown, null, undefined>;

    this.xScale = d3.scaleBand()
      .padding(0.1)
      .domain(this.histogram.values.map(x => x.name))
      .range([0, width]);

    this.scaleYAxis = this.histogram.logScaleY ? d3.scaleLog() : d3.scaleLinear();
    this.scaleYAxis.range([height, 0]).domain([1, d3.max(this.histogram.values.map(v => v.value))]);

    this.redrawXAxis(svg, width, height);

    const leftAxis = d3.axisLeft(this.scaleYAxis);
    leftAxis.ticks(3, '.0f');
    svg.append('g')
      .call(leftAxis);
    svg.selectAll('bar')
      .data(this.histogram.values)
      .enter().append('rect')
      .style('fill', 'steelblue')
      .attr('x', (v: { name: string, value: number }) => this.xScale(v.name))
      .attr('width', this.xScale.bandwidth())
      .attr('y', (v: { name: string, value: number }) => v.value === 0 ? height : this.scaleYAxis(v.value))
      .attr('height', (v: { name: string, value: number }) =>
        v.value === 0 || v.value === undefined ? 0 : height - this.scaleYAxis(v.value));
    this.svg = svg;
  }

  private redrawXAxis(
    svg: d3.Selection<SVGElement, unknown, null, undefined>,
    width: number,
    height: number
  ): void {
    const axisX = [0];
    const axisVals = [];

    for (let i = 0; i < this.histogram.values.length - 1; i++) {
      const leftX = this.xScale(i.toString()) - this.xScale.step() * this.xScale.paddingOuter() / 2;
      axisX.push(leftX);
      axisVals.push(this.histogram.values[i].name);
    }

    this.scaleXAxis = d3.scaleThreshold().range(axisX).domain(axisVals);

    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(
        d3.axisBottom(this.scaleXAxis)
          .tickValues(this.histogram.values.map(v => v.value))
      ).style('font-size', '12px');
  }

  public get viewBox(): string {
    const pos = true ? '0 0' : '-8 -8';
    return `${pos} ${this.width} ${this.height}`;
  }

  private transform(value: number): string {
    if (!value) {
      return '0';
    }
    if (value < 1e-4) {
      return value.toExponential(2);
    } else {
      return value.toFixed(3);
    }
  }
}
