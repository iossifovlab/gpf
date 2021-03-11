import { Component, ViewChild, SimpleChanges, SimpleChange } from '@angular/core';
import { By } from '@angular/platform-browser';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Observable, ReplaySubject, of } from 'rxjs';
import * as d3 from 'd3';

import { FormsModule } from '@angular/forms';
import { HistogramComponent } from './histogram.component';
import { HistogramRangeSelectorLineComponent } from './histogram-range-selector-line.component';

@Component({
  template: `
      <gpf-histogram #gpfhistogram
		    width="650" height="145"
		    [bins]="bins"
        [bars]="bars"
        [domainMin]="domainMin"
        [domainMax]="domainMax"
		    [rangesCounts]="rangesCounts | async"
		    [(rangeStart)]="rangeStart" [(rangeEnd)]="rangeEnd">
		  </gpf-histogram>
    `
})
class TestHostComponent {
  bins = [1, 2, 3, 4];
  bars = [2, 3, 4, 5];
  rangeStart = 2;
  rangeEnd = 4;
  domainMin = 1;
  domainMax = 12;
  rangesCounts: Observable<Array<number>> = of([2, 7, 5]);

  @ViewChild('gpfhistogram') histogramEl;
}

@Component({
  template: `
      <gpf-histogram #gpfhistogram
		    width="650" height="145"
		    [bins]="bins"
        [bars]="bars"
        [domainMin]="domainMin"
        [domainMax]="domainMax"
		    [rangesCounts]="rangesCounts | async"
		    [(rangeStart)]="rangeStart" [(rangeEnd)]="rangeEnd">
		  </gpf-histogram>
    `
})
class TestHostComponentManyBins {
  bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  bars = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
  rangeStart = 2;
  rangeEnd = 4;
  domainMin = 1;
  domainMax = 12;
  isInteractive = true;
  rangesCounts: Observable<Array<number>> = of([2, 7, 56]);

  @ViewChild('gpfhistogram') histogramEl;
}

describe('HistogramComponent', () => {
  let component: TestHostComponent;
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ FormsModule ],
      declarations: [
        HistogramComponent, HistogramRangeSelectorLineComponent,
        TestHostComponent,
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestHostComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render an svg', () => {
    expect(d3.select('svg')).not.toBeNull();
  });

  it('should have the correct width and height', () => {
    expect(d3.select('svg').attr('width')).toEqual('650');
    expect(d3.select('svg').attr('height')).toEqual('145');
  });

  it('should render the correct amount of bars', async(() => {
    fixture.whenStable().then(() => {
      expect(d3.select('svg').selectAll('rect').nodes().length).toEqual(4);
    });
  }));

  it('should redraw the histogram on changes', async(() => {
    spyOn(component.histogramEl, 'redrawHistogram').and.callThrough();
    const bins = [7, 8, 9, 10];
    const bars = [8, 9, 10, 11];
    const binsChange = new SimpleChange(component.bins, bins, true);
    const barsChange = new SimpleChange(component.bars, bars, true);
    const changes = {bins: binsChange, bars: barsChange};
    component.histogramEl.ngOnChanges(changes as SimpleChanges);
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(component.histogramEl.redrawHistogram).toHaveBeenCalledTimes(1);
    });
  }));

  it('should render a correct label with the sum of bars within the range', async(() => {
    fixture.whenStable().then(() => {
      const sumOfBarsLabelEl = fixture.debugElement.query(By.css('#sumOfBarsLabel'));
      expect(sumOfBarsLabelEl).not.toBeNull();
      expect(sumOfBarsLabelEl.nativeElement.innerHTML).toEqual('7 (50.00%)');
    });
  }));

  it('should render sliders', async(() => {
    const sliderEls = fixture.debugElement.queryAll((el) => el.nativeElement.attributes.getNamedItem('gpf-histogram-range-selector-line'));
    expect(sliderEls.length).toBe(2);
  }));

  it('should set the correct labels to the sliders', () => {
    const sliderLabels = fixture.debugElement.queryAll(By.css('.partitions-text'));
    const sliderLabelsText = sliderLabels.map((label) => label.nativeElement.innerHTML);
    expect(sliderLabels.length).toBe(3);
    expect(sliderLabelsText.length).toBe(3);
    expect(sliderLabelsText).toEqual(jasmine.arrayContaining(['2 (14.29%)', '5 (35.71%)', '7 (50.00%)']));
  });

  it('should not render range input fields if less than 10 bins', async(() => {
    const rangeInputElFrom = fixture.debugElement.query(By.css('.histogram-from'));
    const rangeInputElTo = fixture.debugElement.query(By.css('.histogram-to'));
    expect(rangeInputElFrom).toBeNull();
    expect(rangeInputElTo).toBeNull();
  }));
});

describe('HistogramComponentManyBins', () => {
  let component: TestHostComponentManyBins;
  let fixture: ComponentFixture<TestHostComponentManyBins>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ FormsModule ],
      declarations: [
        HistogramComponent, HistogramRangeSelectorLineComponent,
        TestHostComponentManyBins,
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestHostComponentManyBins);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render range input fields if 10 or more bins', () => {
    const rangeInputElFrom = fixture.debugElement.query(By.css('.histogram-from'));
    const rangeInputElTo = fixture.debugElement.query(By.css('.histogram-to'));
    expect(rangeInputElFrom).not.toBeNull();
    expect(rangeInputElTo).not.toBeNull();
  });

  it('should render buttons for the range input fields', () => {
    const rangeInputElFrom = fixture.debugElement.query(By.css('.histogram-from'));
    const rangeInputElTo = fixture.debugElement.query(By.css('.histogram-to'));
    expect(rangeInputElFrom.queryAll(By.css('button')).length).toBe(2);
    expect(rangeInputElFrom.query(By.css('.step.up'))).not.toBeNull();
    expect(rangeInputElFrom.query(By.css('.step.down'))).not.toBeNull();
    expect(rangeInputElTo.queryAll(By.css('button')).length).toBe(2);
    expect(rangeInputElTo.query(By.css('.step.up'))).not.toBeNull();
    expect(rangeInputElTo.query(By.css('.step.down'))).not.toBeNull();
  });

});
