import { SimpleChanges, SimpleChange } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import * as d3 from 'd3';

import { FormsModule } from '@angular/forms';
import { HistogramComponent } from './histogram.component';
import { HistogramRangeSelectorLineComponent } from './histogram-range-selector-line.component';

describe('HistogramComponent', () => {
  let component: HistogramComponent;
  let fixture: ComponentFixture<HistogramComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [
        HistogramComponent, HistogramRangeSelectorLineComponent
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(HistogramComponent);
    component = fixture.componentInstance;

    component.bins = [1, 2, 3, 4];
    component.bars = [2, 3, 4, 5];
    component.rangeStart = 2;
    component.rangeEnd = 4;
    component.domainMin = -20;
    component.domainMax = 20;
    component.xScale = d3.scaleBand()
      .padding(0.1)
      .domain(Array.from(component.bars.keys()).map(x => x.toString()))
      .range([0, 450.0]);
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should redraw the histogram on changes', () => {
    const bins = [7, 8, 9, 10];
    const bars = [8, 9, 10, 11];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};

    component.ngOnChanges(changes as SimpleChanges);
    fixture.detectChanges();

    expect(component.xScale.domain()).toStrictEqual(['0', '1', '2', '3']);
    expect(component.xScale.range()).toStrictEqual([0, 450.0]);
    expect(component.xScale.padding()).toBe(0.1);

    expect(component.scaleYAxis.domain()).toStrictEqual([0, 11]);
    expect(component.scaleYAxis.range()).toStrictEqual([50, 0]);

    expect(component.scaleXAxis.domain()).toStrictEqual([7, 8, 9, Infinity]);
    expect(component.scaleXAxis.range()).toStrictEqual([
      0,
      60.36585365853659,
      170.1219512195122,
      279.8780487804878,
      450
    ]);
  });

  it('should redraw the histogram when bins are more than 10', () => {
    const bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];
    const bars = [-20, -19.7, -19.4, -19.1, -18.8, -18.5, -18.2, -17.9, -17.6, -17.3, -17, -16.7, -16.4];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};

    component.ngOnChanges(changes as SimpleChanges);

    expect(component.xScale.domain()).toStrictEqual(
      ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13']
    );
    expect(component.xScale.range()).toStrictEqual([0, 450.0]);
    expect(component.xScale.padding()).toBe(0.1);

    expect(component.scaleYAxis.domain()).toStrictEqual([0, -16.4]);
    expect(component.scaleYAxis.range()).toStrictEqual([50, 0]);

    expect(component.scaleXAxis.domain()).toStrictEqual(bins);
    expect(component.scaleXAxis.range()).toStrictEqual([
      0,
      1.5957446808510467,
      33.510638297872326,
      65.4255319148936,
      97.34042553191487,
      129.25531914893617,
      161.17021276595744,
      193.08510638297872,
      225,
      256.9148936170213,
      288.82978723404256,
      320.74468085106383,
      352.6595744680851,
      384.5744680851064,
      450
    ]);
  });

  it('should draw the histogram with log scale Y', () => {
    const bins = [1, 2, 3];
    const bars = [9, 10, 11];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};

    component.logScaleY = true;

    component.ngOnChanges(changes as SimpleChanges);

    expect(component.xScale.domain()).toStrictEqual(
      ['0', '1', '2']
    );
    expect(component.xScale.range()).toStrictEqual([0, 450.0]);
    expect(component.xScale.padding()).toBe(0.1);

    expect(component.scaleYAxis.domain()).toStrictEqual([1, 11]);
    expect(component.scaleYAxis.range()).toStrictEqual([50, 0]);

    expect(component.scaleXAxis.domain()).toStrictEqual([1, 2, Infinity]);
    expect(component.scaleXAxis.range()).toStrictEqual([
      0,
      79.83870967741937,
      225,
      450
    ]);
  });

  it('should set a correct label with the sum of bars within the range', () => {
    const rangesCounts = [1, 2, 3];
    component.rangesCounts = rangesCounts;

    const bins = [1, 2, 3];
    const bars = [9, 10, 11];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);

    const changes = {bins: binsChange, bars: barsChange};

    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    expect(component.insideRangeText).toBe('~10 (33.33%)');
  });

  it('should set a correct label with the estimate sum of bars within the range', () => {
    const rangesCounts = [1, 2, 3];
    component.rangesCounts = rangesCounts;
    const rangesCountsChange = new SimpleChange(component.rangesCounts, rangesCounts, true);

    const bins = [1, 2, 3];
    const bars = [9, 10, 11];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);

    const changes = {bins: binsChange, bars: barsChange, rangesCounts: rangesCountsChange};

    component.ngOnChanges(changes as SimpleChanges);

    expect(component.insideRangeText).toBe('2 (6.67%)');
  });

  it('should set estimate values as labels to the sliders', () => {
    const rangesCounts = [1, 2, 3];
    component.rangesCounts = rangesCounts;

    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);

    const changes = {bins: binsChange, bars: barsChange};

    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();
    component.selectedStartIndex = 1;
    component.selectedEndIndex = 3;

    expect(component.beforeRangeText).toBe('~9 (16.36%)');
    expect(component.afterRangeText).toBe('~13 (23.64%)');
  });

  it('should hide range input fields if less than 10 bins', () => {
    fixture.detectChanges();
    expect(component.showMinMaxInputWithDefaultValue).toBe(false);
  });

  it('should show range input fields if more than 10 bins', () => {
    const bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];
    const bars = [-20, -19.7, -19.4, -19.1, -18.8, -18.5, -18.2, -17.9, -17.6, -17.3, -17, -16.7, -16.4];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};

    component.ngOnChanges(changes as SimpleChanges);

    expect(component.showMinMaxInputWithDefaultValue).toBe(true);
  });

  it('should set range start, check input value and start slider text', () => {
    const rangeStartEmitSpy = jest.spyOn(component.rangeStartChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();
    component.selectedStartIndex = 1;

    expect(component.rangeStart).toBe(2);
    expect(component.rangeStartDisplay).toBe('2');
    expect(component.beforeRangeText).toBe('~9 (16.36%)');
    expect(rangeStartEmitSpy).toHaveBeenCalledWith(2);
  });

  it('should set range end, check input value and end slider text', () => {
    const rangeEndEmitSpy = jest.spyOn(component.rangeEndChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();
    component.selectedEndIndex = 2;

    expect(component.rangeEnd).toBe(4);
    expect(component.rangeEndDisplay).toBe('4');
    expect(component.afterRangeText).toBe('~25 (45.45%)');
    expect(rangeEndEmitSpy).toHaveBeenCalledWith(4);
  });

  it('should set first bin as range start when range start is set to null', () => {
    const rangeStartEmitSpy = jest.spyOn(component.rangeStartChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    component.setRangeStartFromInput(null);
    expect(component.rangeStart).toBe(1);
    expect(component.rangeStartDisplay).toBe('');
    expect(component.beforeRangeText).toBe('~0 (0.00%)');
    expect(rangeStartEmitSpy).toHaveBeenCalledWith(1);
  });

  it('should set range start to first bin when parent set it to null', () => {
    const rangeStartEmitSpy = jest.spyOn(component.rangeStartChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const rangeStartChange = new SimpleChange(component.rangeStart, null, true);
    component.rangeStart = null;
    const changes = {bins: binsChange, bars: barsChange, rangeStart: rangeStartChange};

    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    expect(component.rangeStart).toBe(1);
    expect(component.rangeStartDisplay).toBe('1');
    expect(rangeStartEmitSpy).not.toHaveBeenCalledWith();
  });

  it('should set range end to last bin when parent set it to null', () => {
    const rangeEndEmitSpy = jest.spyOn(component.rangeEndChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const rangeEndChange = new SimpleChange(component.rangeEnd, null, true);
    component.rangeEnd = null;
    const changes = {bins: binsChange, bars: barsChange, rangeEnd: rangeEndChange};

    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    expect(component.rangeEnd).toBe(5);
    expect(component.rangeEndDisplay).toBe('5');
    expect(rangeEndEmitSpy).not.toHaveBeenCalledWith();
  });


  it('should set last bin as range end when range end is set to null', () => {
    const rangeEndEmitSpy = jest.spyOn(component.rangeEndChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    component.setRangeEndFromInput(null);
    expect(component.rangeEnd).toBe(5);
    expect(component.rangeEndDisplay).toBe('');
    expect(component.afterRangeText).toBe('~13 (23.64%)');
    expect(rangeEndEmitSpy).toHaveBeenCalledWith(5);
  });

  it('should get default labels of x axis when bins are less than 10', () => {
    expect(component.xLabelsWithDefaultValue).toStrictEqual([1, 2, 3]);
  });

  it('should get default labels of x axis when bins are more than 10', () => {
    const bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];
    const bars = [-20, -19.7, -19.4, -19.1, -18.8, -18.5, -18.2, -17.9, -17.6, -17.3, -17, -16.7, -16.4];
    component.bins = bins;
    component.bars = bars;

    expect(component.xLabelsWithDefaultValue).toStrictEqual(bins);
  });

  it('should get default labels of x axis when bins are more than 10 and log scale of x is true', () => {
    const bins = [100, 222, 378, 412, 555, 678, 732, 845, 977, 10456, 11433, 12789, 130124, 147896541];
    const bars = [-20, -19.7, -19.4, -19.1, -18.8, -18.5, -18.2, -17.9, -17.6, -17.3, -17, -16.7, -16.4];
    component.bins = bins;
    component.bars = bars;
    component.logScaleX = true;

    expect(component.xLabelsWithDefaultValue).toStrictEqual([
      100,
      1000,
      10000,
      100000,
      1000000,
      10000000,
      100000000
    ]);
  });

  it('should get default labels of x axis when bins are more than 10, log scale x is true and first bin is 0', () => {
    const bins = [0.0, 222, 378, 412, 555, 678, 732, 845, 977, 10456, 11433, 12789, 130124, 147896541];
    const bars = [-20, -19.7, -19.4, -19.1, -18.8, -18.5, -18.2, -17.9, -17.6, -17.3, -17, -16.7, -16.4];
    component.bins = bins;
    component.bars = bars;
    component.logScaleX = true;

    expect(component.xLabelsWithDefaultValue).toStrictEqual([
      1000,
      10000,
      100000,
      1000000,
      10000000,
      100000000
    ]);
  });

  it('should return labels of x axis if they are already set', () => {
    component.xLabels = [1, 2, 3];
    expect(component.xLabelsWithDefaultValue).toStrictEqual([1, 2, 3]);
  });

  it('should set range start via input', () => {
    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.setRangeStartFromInput('2');
    expect(component.rangeStart).toBe(2);
    expect(component.rangeStartDisplay).toBe('2');
    expect(component.beforeRangeText).toBe('~9 (16.36%)');
  });

  it('should set range start with invalid input', () => {
    const rangeStartEmitSpy = jest.spyOn(component.rangeStartChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.rangeStart = null;
    component.ngOnInit();

    component.setRangeStartFromInput('random text');
    expect(component.rangeStart).toBe(1);
    expect(component.rangeStartDisplay).toBe('');
    expect(component.beforeRangeText).toBe('~0 (0.00%)');
    expect(rangeStartEmitSpy).toHaveBeenCalledWith(1);
  });

  it('should set range end via input', () => {
    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.setRangeEndFromInput('4');
    expect(component.rangeEnd).toBe(4);
    expect(component.rangeEndDisplay).toBe('4');
    expect(component.afterRangeText).toBe('~25 (45.45%)');
  });

  it('should set range end with invalid input', () => {
    const rangeEndEmitSpy = jest.spyOn(component.rangeEndChange, 'emit');

    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.rangeEnd = null;
    component.ngOnInit();

    component.setRangeEndFromInput('random text');
    expect(component.rangeEnd).toBe(5);
    expect(component.rangeEndDisplay).toBe('');
    expect(component.afterRangeText).toBe('~13 (23.64%)');
    expect(rangeEndEmitSpy).toHaveBeenCalledWith(5);
  });

  it('should get min value rounded by the forth symbol', () => {
    const bins = [1.365789, 2, 3, 4, 5];
    component.bins = bins;

    expect(component.minValue).toBe(1.3658);
  });

  it('should get max value rounded by the forth symbol', () => {
    const bins = [1, 2, 3, 4, 5.378544];
    component.bins = bins;

    expect(component.maxValue).toBe(5.3785);
  });

  it('should increase range start by 1', () => {
    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5, 6, 7, 8];
    const bars = [9, 10, 11, 12, 13, 14, 15, 16];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    component.selectedEndIndex = 5;
    component.selectedStartIndex = 2;
    component.startStepUp();
    expect(component.selectedStartIndex).toBe(3);
  });

  it('should decrease range start by 1', () => {
    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5, 6, 7, 8];
    const bars = [9, 10, 11, 12, 13, 14, 15, 16];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    component.selectedEndIndex = 5;
    component.selectedStartIndex = 4;
    component.startStepDown();
    expect(component.selectedStartIndex).toBe(3);
  });

  it('should increase range end by 1', () => {
    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5, 6, 7, 8];
    const bars = [9, 10, 11, 12, 13, 14, 15, 16];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    component.selectedEndIndex = 3;
    component.selectedStartIndex = 2;
    component.endStepUp();
    expect(component.selectedEndIndex).toBe(4);
  });

  it('should decrease range end by 1', () => {
    // trigger redrawHistogram() to set sum of bars
    const bins = [1, 2, 3, 4, 5, 6, 7, 8];
    const bars = [9, 10, 11, 12, 13, 14, 15, 16];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.ngOnInit();

    component.selectedEndIndex = 5;
    component.selectedStartIndex = 4;
    component.endStepDown();
    expect(component.selectedEndIndex).toBe(4);
  });

  it('should transform range start slider position into index', () => {
    // trigger redrawHistogram()
    const bins = [1, 2, 3, 4];
    const bars = [9, 10, 11, 12];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.startX = 215;
    expect(component.selectedStartIndex).toBe(2);
  });

  it('should transform range start slider position into index when the slider is moved outside the range', () => {
    // trigger redrawHistogram()
    const bars = [207, 211, 506, 608];
    const bins = [1, 2, 3, 4];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.rangeStart = 3;
    component.startX = 870;

    expect(component.selectedStartIndex).toBe(2);
  });

  it('should transform range end slider position into index', () => {
    // trigger redrawHistogram()
    const bins = [1, 2, 3, 4];
    const bars = [9, 10, 11, 12];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.endX = 215;
    expect(component.selectedEndIndex).toBe(1);
  });

  it('should transform range end slider position into index when the slider is moved outside the range', () => {
    // trigger redrawHistogram()
    const bars = [207, 211, 506, 608];
    const bins = [1, 2, 3, 4];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.rangeEnd = 2;
    component.endX = -130;

    expect(component.selectedEndIndex).toBe(0);
  });

  it('should check if single score is valid', () => {
    component.singleScoreValue = 2;
    expect(component.singleScoreValueIsValid()).toBe(true);

    component.singleScoreValue = undefined;
    expect(component.singleScoreValueIsValid()).toBe(false);

    component.singleScoreValue = null;
    expect(component.singleScoreValueIsValid()).toBe(false);

    component.singleScoreValue = NaN;
    expect(component.singleScoreValueIsValid()).toBe(false);
  });

  it('should set first and last bins as range start and end when mode is not interactive', () => {
    // trigger redrawHistogram()
    const bars = [207, 211, 506, 608];
    const bins = [1, 2, 3, 4];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.isInteractive = false;

    component.ngOnInit();

    expect(component.rangeStart).toBe(1);
    expect(component.rangeEnd).toBe(4);
  });

  it('should emit min value to parent when range start is null', () => {
    const rangeStartEmitSpy = jest.spyOn(component.rangeStartChange, 'emit');

    const bins = [10, 20, 30, 40, 50];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.rangeStart = null;
    component.ngOnInit();

    component.setRangeStartFromInput(null);
    expect(component.minValue).toBe(10);
    expect(rangeStartEmitSpy).toHaveBeenLastCalledWith(10);
  });

  it('should emit max value to parent when range end is null', () => {
    jest.clearAllMocks();
    const rangeEndEmitSpy = jest.spyOn(component.rangeEndChange, 'emit');

    const bins = [11, 13, 15, 17, 19];
    const bars = [9, 10, 11, 12, 13];
    component.bins = bins;
    component.bars = bars;
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.ngOnChanges(changes as SimpleChanges);

    component.rangeEnd = null;
    component.ngOnInit();

    component.setRangeEndFromInput(null);
    expect(component.maxValue).toBe(19);
    expect(rangeEndEmitSpy).toHaveBeenLastCalledWith(19);
  });
});
