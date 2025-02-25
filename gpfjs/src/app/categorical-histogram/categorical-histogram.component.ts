import {
  Input,
  Component,
  ViewChild,
  ChangeDetectionStrategy,
  ElementRef,
  OnChanges,
  Output,
  EventEmitter,
  OnInit
} from '@angular/core';
import { CategoricalHistogramView, CategoricalHistogram } from 'app/utils/histogram-types';

import * as d3 from 'd3';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-categorical-histogram',
  templateUrl: './categorical-histogram.component.html',
  styleUrl: './categorical-histogram.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CategoricalHistogramComponent implements OnChanges, OnInit {
  @Input() public width: number;
  @Input() public height: number;
  @Input() public marginLeft = 100;
  @Input() public marginTop = -40;
  @Input() public interactType: CategoricalHistogramView = 'range selector';
  @ViewChild('histogramContainer', {static: true}) public histogramContainer: ElementRef;

  @Input() public showCounts = true;
  @Input() public showMinMaxInput: boolean;

  @Input() public histogram: CategoricalHistogram;
  @Input() public initialSelectedValueNames: string[] = [];

  // Values used as histogram bars
  public values: {name: string, value: number}[] = [];
  // Omitted values that are combined in one custom bar
  public otherValueNames: string[] = [];
  // Currently selected names of values
  public selectedValueNames: string[] = [];

  private barCount: number;
  private readonly defaultBarCount = 20;
  public labelRotation = 0;

  private svg: d3.Selection<SVGElement, unknown, null, undefined>;

  @Input() public isInteractive = true;
  @Input() public singleScoreValue: string;

  public sliderStartIndex: number = 0;
  public sliderEndIndex: number = 450;
  public valuesBetweenSliders: string[] = [];

  @Output() public selectCategoricalValues = new EventEmitter<string[]>();

  public xScale: d3.ScaleBand<string>;
  public scaleXAxis: d3.ScaleOrdinal<string, number, never>;
  public scaleYAxis: d3.ScaleLinear<number, number, never>
                     | d3.ScaleLogarithmic<number, number, never>;

  public ngOnInit(): void {
    this.calculateBarCount();

    this.values = cloneDeep(this.histogram.values);
    this.formatValues();
    this.labelRotation = this.histogram.labelRotation;

    // Select all values if no initial are provided and range selector mode is used
    if (this.initialSelectedValueNames.length) {
      this.selectedValueNames = cloneDeep(this.initialSelectedValueNames);
      this.formatSelectedValueNames();
    } else if (this.interactType === 'range selector') {
      this.selectedValueNames = this.values.map(v => v.name);
      this.selectCategoricalValues.emit(this.histogram.values.map(v => v.name));
    }

    // Redraw histogram
    this.sliderStartIndex = 0;
    this.sliderEndIndex = this.values.length - 1;
    this.redrawHistogram();

    // Redraw histogram sliders if range selector mode
    if (this.interactType === 'range selector') {
      this.redrawSliders(this.selectedValueNames);
    }
  }

  public ngOnChanges(): void {
    if (this.values.length) {
      this.selectedValueNames = cloneDeep(this.initialSelectedValueNames);
      this.formatSelectedValueNames();
      this.redrawHistogram();
    }
  }

  private calculateBarCount(): void {
    this.barCount = this.histogram.values.length;
    if (this.histogram.displayedValuesCount) {
      this.barCount = this.histogram.displayedValuesCount;
    } else if (this.histogram.displayedValuesPercent) {
      this.barCount = Math.floor(this.histogram.values.length / 100 * this.histogram.displayedValuesPercent);
    } else {
      this.barCount = this.defaultBarCount;
    }
  }

  // Sort and combine other values
  private formatValues(): void {
    this.values.sort((a, b) => {
      return this.histogram.valueOrder.indexOf(a.name) - this.histogram.valueOrder.indexOf(b.name);
    });

    if (this.barCount < this.values.length) {
      const otherValues = this.values
        .splice(this.barCount, this.values.length);
      this.otherValueNames = otherValues.map(v => v.name);
      const otherSum = otherValues.reduce((acc, v) => acc + v.value, 0);
      this.values.push({name: 'Other values', value: otherSum});
    }
  }

  // Sort and combine other values
  private formatSelectedValueNames(): void {
    this.selectedValueNames.sort((a, b) => {
      return this.histogram.valueOrder.indexOf(a) - this.histogram.valueOrder.indexOf(b);
    });
    if (this.otherValueNames.length) {
      const visibleValues = [...new Set(this.selectedValueNames).difference(new Set(this.otherValueNames))];

      if (this.selectedValueNames.length - visibleValues.length === this.otherValueNames.length) {
        visibleValues.push('Other values');
      }
      this.selectedValueNames = visibleValues;
    }
  }

  public singleScoreValueIsValid(): boolean {
    return this.singleScoreValue !== undefined
      && this.singleScoreValue !== null
      && this.singleScoreValue !== '';
  }

  private redrawHistogram(): void {
    d3.select(this.histogramContainer.nativeElement).selectAll('g').remove();
    d3.select(this.histogramContainer.nativeElement).selectAll('rect').remove();

    const width = 450.0;
    const height = 50;

    const svg = d3.select(
      this.histogramContainer.nativeElement
    ) as d3.Selection<SVGElement, unknown, null, undefined>;

    this.xScale = d3.scaleBand()
      .padding(0.1)
      .domain(this.values.map(v => v.name))
      .range([0, width]);

    this.scaleYAxis = this.histogram.logScaleY ? d3.scaleLog() : d3.scaleLinear();
    this.scaleYAxis.range([height, 0]).domain([1, d3.max(this.values.map(v => v.value))]);

    this.redrawXAxis(svg, width, height);

    const leftAxis = d3.axisLeft(this.scaleYAxis);
    leftAxis.ticks(3, '.0f');
    svg.append('g')
      .call(leftAxis);
    svg.selectAll('bar')
      .data(this.values)
      .enter().append('rect')
      .style('fill', 'lightsteelblue')
      .attr('x', (v: { name: string, value: number }) => this.xScale(v.name))
      .attr('width', this.xScale.bandwidth())
      .attr('y', (v: { name: string, value: number }) => v.value === 0 ? height : this.scaleYAxis(v.value))
      .attr('height', (v: { name: string, value: number }) =>
        v.value === 0 || v.value === undefined ? 0 : height - this.scaleYAxis(v.value))
      .attr('id', (v: { name: string, value: number }) => v.name);

    if (this.interactType === 'click selector') {
      svg.selectAll('rect').on('click', event => {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
        this.toggleValue(event);
      });

      svg.selectAll('rect').on('mouseover', (element: MouseEvent) => {
        (element.target as SVGRectElement).style.filter = 'brightness(75%)';
        (element.target as SVGRectElement).style.cursor = 'pointer';
      }).on('mouseout', (element: MouseEvent) => {
        (element.target as SVGRectElement).style.filter = 'none';
        (element.target as SVGRectElement).style.cursor = 'default';
      });
    }

    if (this.selectedValueNames.length > 0) {
      this.selectedValueNames.forEach(name => {
        svg.select(`[id="${name}"]`)
          .style('fill', 'steelblue');
      });
    }
    this.svg = svg;
  }

  private redrawXAxis(
    svg: d3.Selection<SVGElement, unknown, null, undefined>,
    width: number,
    height: number,
  ): void {
    const axisX: number[] = [0];
    const axisVals: string[] = [''];

    this.values.forEach(value => {
      const leftX = this.xScale(value.name) + this.xScale.bandwidth() / 2;
      axisX.push(leftX);
      axisVals.push(value.name);
    });

    axisX.push(width);
    axisVals.push('');
    this.scaleXAxis = d3.scaleOrdinal(axisVals, axisX);
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(
        d3.axisBottom(this.scaleXAxis)
      ).style('font-size', '12px');
    svg.selectAll('text').style('text-anchor', 'start').attr('transform', `rotate(${this.labelRotation})`);
    // add hover text on each label
    this.values.forEach(value => {
      svg.selectAll('text').filter(t => t === value.name).append('title').text(value.name);
    });
  }

  private toggleValue(event: { srcElement: { id: string, style: { fill: string } } }): void {
    if (event.srcElement.style.fill === 'steelblue') {
      event.srcElement.style.fill = 'lightsteelblue';
    } else {
      event.srcElement.style.fill = 'steelblue';
    }

    if (event.srcElement.id !== 'Other values') {
      this.selectCategoricalValues.emit([event.srcElement.id]);
    } else {
      this.selectCategoricalValues.emit(this.otherValueNames);
    }
  }

  private colorBars(): void {
    this.svg.selectAll('rect').style('fill', (b: {name: string, value: number}) => {
      const i = this.values.findIndex(bar => bar.name === b.name);
      return i < this.sliderStartIndex || i > this.sliderEndIndex
        ? 'lightsteelblue' : 'steelblue';
    });
  }

  public get viewBox(): string {
    let pos = '-30 -8';
    if (this.labelRotation === 0) {
      pos = '-30 -60';
    }
    return `${pos} ${this.width} ${this.height}`;
  }

  private redrawSliders(selectedValues: string[]): void {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();

    this.sliderStartIndex = this.values.findIndex(v =>
      v.name === selectedValues[0]);
    this.sliderEndIndex = this.values.findIndex(v =>
      v.name === selectedValues[selectedValues.length-1]);

    this.startX = this.xScale(selectedValues[0])
      - distBetweenBars / 2 - 1;

    this.endX = this.xScale(selectedValues[selectedValues.length-1])
      + this.xScale.bandwidth() + distBetweenBars / 2 - 1;

    this.colorBars();
  }

  public get startX(): number {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    const name = this.values.at(this.sliderStartIndex).name;
    return this.xScale(name) - distBetweenBars / 2 - 1;
  }

  public set startX(newPositionX) {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    const newStartIndex = this.getClosestIndexByX(newPositionX + distBetweenBars / 2 + 1);
    if (newStartIndex === this.sliderStartIndex || newStartIndex > this.sliderEndIndex) {
      return;
    }

    this.toggleValuesInRange(this.sliderStartIndex, newStartIndex);
    this.sliderStartIndex = newStartIndex;
    this.colorBars();
  }

  public get endX(): number {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    const name = this.values.at(this.sliderEndIndex).name;
    return this.xScale(name) + this.xScale.bandwidth() + distBetweenBars / 2 - 1;
  }

  public set endX(newPositionX) {
    const distBetweenBars = this.xScale.step() * this.xScale.paddingInner();
    const newEndIndex = this.getClosestIndexByX(newPositionX - this.xScale.bandwidth() - distBetweenBars / 2 + 1);
    if (newEndIndex === this.sliderEndIndex || newEndIndex < this.sliderStartIndex) {
      return;
    }

    // Uses +1 because end slider is offset by 1 compared to start slider
    this.toggleValuesInRange(this.sliderEndIndex + 1, newEndIndex + 1);
    this.sliderEndIndex = newEndIndex;
    this.colorBars();
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

  private toggleValuesInRange(a: number, b: number): void {
    const start = Math.min(a, b);
    const end = Math.max(a, b);
    let toggled = this.values.slice(start, end).map(v => v.name);
    const otherIndex = toggled.findIndex(name => name === 'Other values');
    if (otherIndex !== -1) {
      toggled.splice(otherIndex, 1);
      toggled = [...toggled, ...this.otherValueNames];
    }
    this.selectCategoricalValues.emit(toggled);
    this.colorBars();
  }
}
