import {
  Input,
  Component, OnInit,
  OnChanges,
  ViewChild,
  Output,
  EventEmitter,
  SimpleChanges,
  ChangeDetectionStrategy,
  ElementRef
} from '@angular/core';

import * as d3 from 'd3';
import { Subject } from 'rxjs';

interface BinBar {
  index: number;
  bin: number;
  bar: number;
}

@Component({
  selector: 'gpf-histogram',
  templateUrl: './histogram.component.html',
  styleUrls: ['./histogram.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HistogramComponent implements OnInit, OnChanges {
  private rangeStartSubject = new Subject<number>();
  private rangeEndSubject = new Subject<number>();

  private internalRangeStart: number;
  private internalRangeEnd: number;

  private internalRangeStartField: number;
  private internalRangeEndField: number;

  @Output() public rangeStartChange = new EventEmitter();
  @Output() public rangeEndChange = new EventEmitter();

  @Input() public width: number;
  @Input() public height: number;
  @Input() public marginLeft = 100;
  @Input() public marginTop = 10;
  @ViewChild('histogramContainer', {static: true}) public histogramContainer: ElementRef;

  @Input() public bins: Array<number>;
  @Input() public bars: Array<number>;
  @Input() public domainMin: number;
  @Input() public domainMax: number;

  @Input() public logScaleX = false;
  @Input() public logScaleY = false;
  @Input() public showCounts = true;
  @Input() public xLabels: Array<number>;
  @Input() public centerLabels: boolean;
  @Input() public showMinMaxInput: boolean;

  @Input() public largeValuesDesc: string;
  @Input() public smallValuesDesc: string;

  public beforeRangeText: string;
  public insideRangeText: string;
  public afterRangeText: string;

  public xScale: d3.ScaleBand<string>;
  private barsTotalSum: number;

  private svg: d3.Selection<SVGElement, unknown, null, undefined>;

  private resetRange = false;

  @Input() public isInteractive = true;
  @Input() public singleScoreValue: number;

  public scaleXAxis: d3.ScaleThreshold<number, number, never>;
  public scaleYAxis: d3.ScaleLinear<number, number, never>
                     | d3.ScaleLogarithmic<number, number, never>;

  public ngOnInit(): void {
    this.rangeStartSubject.subscribe((start) => this.rangeStartChange.emit(start));
    this.rangeEndSubject.subscribe((end) => this.rangeEndChange.emit(end));
    this.rangeStartSubject.next(this.rangeStart !== null ? this.rangeStart : this.minValue);
    this.rangeEndSubject.next(this.rangeEnd !== null ? this.rangeEnd : this.maxValue);

    if (!this.isInteractive) {
      this.rangeStart = this.bins[0];
      this.rangeEnd = this.bins[this.bins.length - 1];
    }

    this.estimateRangeTexts();
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if ('bins' in changes || 'bars' in changes) {
      const bins: Array<number> = [];
      const bars: Array<number> = [];
      for (let i = 0; i < this.bins.length; i++) {
        if (this.bins[i] < this.domainMin || this.bins[i] > this.domainMax) {
          continue;
        }
        bins.push(this.bins[i]);
        bars.push(this.bars[i]);
      }
      this.bins = bins;
      this.bars = bars;
      d3.select(this.histogramContainer.nativeElement).selectAll('g').remove();
      d3.select(this.histogramContainer.nativeElement).selectAll('rect').remove();
      this.redrawHistogram();
      if (this.resetRange) {
        this.rangeStart = null;
        this.rangeEnd = null;
      }
      this.resetRange = true;
    }
  }

  public singleScoreValueIsValid(): boolean {
    return this.singleScoreValue !== undefined && this.singleScoreValue !== null && !isNaN(this.singleScoreValue);
  }

  public get showMinMaxInputWithDefaultValue(): boolean {
    if (this.showMinMaxInput === undefined) {
      if (this.bins.length < 10) {
        return false;
      } else {
        return true;
      }
    }
    return this.showMinMaxInput;
  }

  public get centerLabelsWithDefaultValue(): boolean {
    if (this.centerLabels === undefined) {
      if (this.bins.length < 10) {
        return true;
      } else {
        return false;
      }
    }
    return this.centerLabels;
  }

  public get xLabelsWithDefaultValue(): number[] {
    if (this.xLabels === undefined) {
      if (this.bins.length < 10) {
        return this.bins.slice(0, -1);
      } else {
        if (!this.logScaleX) {
          return d3.ticks(this.bins[0], this.bins[this.bins.length - 1], 10);
        }
        const domainMin = this.bins[0] === 0.0 ? this.bins[1] : this.bins[0];
        const domainMax = this.bins[this.bins.length - 1];

        const magnitudeMin = Math.log10(domainMin);
        const magnitudeMax = Math.log10(domainMax);
        const count = Math.min(10, Math.floor(Math.abs(magnitudeMax - magnitudeMin)));

        return d3.scaleLog().domain([domainMin, domainMax]).ticks(count);
      }
    }
    return this.xLabels;
  }

  private onRangeChange(): void {
    if (!this.xScale) {
      return;
    }

    this.estimateRangeTexts();
    this.colorBars();
  }

  private colorBars(): void {
    this.svg.selectAll('rect').style('fill', (d: BinBar) =>
      d.index < this.selectedStartIndex || d.index > this.selectedEndIndex
        ? 'lightsteelblue' : 'steelblue');
  }

  private formatEstimateText(count: number): string {
    const perc = count / this.barsTotalSum * 100;

    if (this.showCounts) {
      return count.toFixed(0) + ' (' + perc.toFixed(2) + '%)';
    } else {
      return perc.toFixed(2) + '%';
    }
  }

  private estimateRangeTexts(): void {
    const beforeRangeCount = d3.sum(this.bars.slice(0, this.selectedStartIndex));
    const insideRangeCount = d3.sum(this.bars.slice(this.selectedStartIndex, this.selectedEndIndex + 1));
    const afterRangeCount = d3.sum(this.bars.slice(this.selectedEndIndex + 1));

    this.beforeRangeText = this.formatEstimateText(beforeRangeCount);
    this.insideRangeText = this.formatEstimateText(insideRangeCount);
    this.afterRangeText = this.formatEstimateText(afterRangeCount);
  }

  private redrawHistogram(): void {
    this.barsTotalSum = d3.sum(this.bars);

    const barsBinsArray: BinBar[] = [];
    for (let i = 0; i < this.bars.length; i++) {
      barsBinsArray[i] = {
        index: i,
        bin: this.bins[i],
        bar: this.bars[i]
      };
    }

    const width = 450.0;
    const height = 50;

    const svg = d3.select(
      this.histogramContainer.nativeElement
    ) as d3.Selection<SVGElement, unknown, null, undefined>;

    this.xScale = d3.scaleBand()
      .padding(0.1)
      .domain(Array.from(this.bars.keys()).map(x => x.toString()))
      .range([0, width]);

    this.scaleYAxis = this.logScaleY ? d3.scaleLog() : d3.scaleLinear();
    this.scaleYAxis.range([height, 0]).domain([1, d3.max(this.bars)]);

    this.redrawXAxis(svg, width, height);

    const leftAxis = d3.axisLeft(this.scaleYAxis);
    leftAxis.ticks(3, '.0f');
    svg.append('g')
      .call(leftAxis);
    svg.selectAll('bar')
      .data(barsBinsArray)
      .enter().append('rect')
      .style('fill', 'steelblue')
      .attr('x', (d: BinBar) => this.xScale(d.index.toString()))
      .attr('width', this.xScale.bandwidth())
      .attr('y', (d: BinBar) => d.bar === 0 ? height : this.scaleYAxis(d.bar))
      .attr('height', (d: BinBar) => d.bar === 0 || d.bar === undefined ? 0 : height - this.scaleYAxis(d.bar));
    this.svg = svg;
    this.colorBars();
  }

  private redrawXAxis(
    svg: d3.Selection<SVGElement, unknown, null, undefined>,
    width: number,
    height: number
  ): void {
    const axisX = [0];
    const axisVals = [];

    for (let i = 0; i < this.bins.length - 1; i++) {
      let leftX: number;
      if (this.centerLabelsWithDefaultValue) {
        leftX = this.xScale(i.toString()) + this.xScale.bandwidth() / 2;
      } else {
        leftX = this.xScale(i.toString()) - this.xScale.step() * this.xScale.paddingOuter() / 2;
      }
      axisX.push(leftX);
      axisVals.push(this.bins[i]);
    }

    if (this.centerLabelsWithDefaultValue) {
      axisX.push(width);
      axisVals.push(Number.POSITIVE_INFINITY);
    } else {
      axisX.push(width);
      axisVals.push(this.bins[this.bins.length - 1]);
    }

    this.scaleXAxis = d3.scaleThreshold().range(axisX).domain(axisVals);
    const formatter = this.createFormatterFunction(5);

    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(
        d3.axisBottom(this.scaleXAxis)
          .tickValues(this.xLabelsWithDefaultValue)
          .tickFormat((_, i) => formatter(this.xLabelsWithDefaultValue[i]))
      ).style('font-size', '12px');
  }

  @Input()
  public set rangeStart(rangeStart) {
    if (rangeStart !== this.internalRangeStart) {
      this.setRangeStart(rangeStart);
      this.internalRangeStartField = Number(this.transform(this.internalRangeStart));
    }
  }

  public get rangeStart(): number {
    return this.internalRangeStart;
  }

  private setRangeStart(rangeStart: number): void {
    if (rangeStart === null) {
      this.internalRangeStart = this.bins[0];
    } else {
      this.internalRangeStart = rangeStart;
    }
    this.onRangeChange();
    this.rangeStartSubject.next(this.internalRangeStart);
  }

  @Input()
  public set rangeEnd(rangeEnd) {
    if (rangeEnd !== this.internalRangeEnd) {
      this.setRangeEnd(rangeEnd);
      this.internalRangeEndField = Number(this.transform(this.internalRangeEnd));
    }
  }

  public get rangeEnd(): number {
    return this.internalRangeEnd;
  }

  private setRangeEnd(rangeEnd: number): void {
    if (rangeEnd === null) {
      this.internalRangeEnd = this.bins[this.bins.length - 1];
    } else {
      this.internalRangeEnd = rangeEnd;
    }
    this.onRangeChange();
    this.rangeEndSubject.next(this.internalRangeEnd);
  }

  public set rangeStartWithoutNull(rangeStart: string) {
    const rangeStartFloat = parseFloat(rangeStart);
    if (!isNaN(rangeStartFloat)) {
      this.setRangeStart(parseFloat(rangeStart));
    } else {
      this.setRangeStart(null);
    }
  }

  public get rangeStartWithoutNull(): string {
    return this.internalRangeStartField.toString();
  }

  public set rangeEndWithoutNull(rangeEnd: string) {
    const rangeEndFloat = parseFloat(rangeEnd);
    if (!isNaN(rangeEndFloat)) {
      this.setRangeEnd(parseFloat(rangeEnd));
    } else {
      this.setRangeEnd(null);
    }
  }

  public get rangeEndWithoutNull(): string {
    return this.internalRangeEndField.toString();
  }

  public get minValue(): number {
    return Number(this.bins[0].toFixed(4));
  }

  public get maxValue(): number {
    return Number(this.bins[this.bins.length - 1].toFixed(4));
  }

  public startStepUp(): void {
    this.selectedStartIndex += 1;
  }

  public startStepDown(): void {
    this.selectedStartIndex -= 1;
  }

  public endStepUp(): void {
    this.selectedEndIndex += 1;
  }

  public endStepDown(): void {
    this.selectedEndIndex -= 1;
  }

  public set selectedStartIndex(index: number) {
    if (index < 0 || index > this.selectedEndIndex) {
      return;
    }
    this.rangeStart = this.bins[index];
  }

  public get selectedStartIndex(): number {
    if (this.rangeStart === null) {
      return 0;
    }
    const maxIndex = this.bins.length - 2;
    const closest = this.getClosestIndexByValue(this.rangeStart);
    return Math.min(maxIndex, closest);
  }

  public set selectedEndIndex(index: number) {
    if (index < this.selectedStartIndex || index >= this.bars.length - 1) {
      return;
    }
    this.rangeEnd = this.bins[index + 1];
  }

  public get selectedEndIndex(): number {
    if (this.rangeEnd === null) {
      return this.bins.length - 2;
    }
    return Math.max(0, this.getClosestIndexByValue(this.rangeEnd) - 1);
  }

  private getClosestIndexByX(x: number): number {
    // Domain uses bins count which is larger than bars by 1 element
    const maxIndex = this.xScale.domain().length;
    for (let i = 1; i < maxIndex; i++) {
      const prevVal = (i - 1) * this.xScale.step();
      const currVal = i * this.xScale.step();
      if (currVal > x) {
        const prev = Math.abs(x - prevVal);
        const curr = Math.abs(x - currVal);
        return prev < curr ? i - 1 : i;
      }
    }
    return maxIndex - 1;
  }

  private getClosestIndexByValue(val: number): number {
    for (let i = 1; i < this.bins.length - 1; i++) {
      if (this.bins[i] >= val) {
        const prev = Math.abs(val - this.bins[i - 1]);
        const curr = Math.abs(val - this.bins[i]);
        return prev < curr ? i - 1 : i;
      }
    }
    return this.bins.length - 1;
  }

  public get startX(): number {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    return this.xScale(this.selectedStartIndex.toString()) - distBetweenBars / 2 - 1;
  }

  public set startX(newPositionX) {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    this.selectedStartIndex = this.getClosestIndexByX(newPositionX + distBetweenBars / 2 + 1);
  }

  public get endX(): number {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    return this.xScale(this.selectedEndIndex.toString()) + this.xScale.bandwidth() + distBetweenBars / 2 - 1;
  }

  public set endX(newPositionX) {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    this.selectedEndIndex = this.getClosestIndexByX(newPositionX - this.xScale.bandwidth() - distBetweenBars / 2 + 1);
  }

  public get viewBox(): string {
    const pos = this.showMinMaxInputWithDefaultValue ? '0 0' : '-8 -8';
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

  private createFormatterFunction(digitCount: number): (num: number) => string {
    // used to add e-6 scientific notation
    const rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
    return (num) => {
      if (num !== 1E-6) {
        return num.toString();
      }
      let value = num / 1E-6;
      value = Number(value.toFixed(digitCount));
      value = Number(String(value).replace(rx, '$1'));
      return `${value}e-6`;
    };
  }
}
