import { Component, ViewChild, SimpleChanges, SimpleChange } from '@angular/core';
import { By } from '@angular/platform-browser';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Observable, of } from 'rxjs';
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
  public bins = [1, 2, 3, 4];
  public bars = [2, 3, 4, 5];
  public rangeStart = 2;
  public rangeEnd = 4;
  public domainMin = 1;
  public domainMax = 12;
  public rangesCounts: Observable<Array<number>> = of([2, 7, 5]);

  @ViewChild('gpfhistogram') public histogramEl;
}

@Component({
  template: `
    <gpf-histogram #gpfhistogram
      width="650" height="145"
      [bins]="bins"
      [bars]="bars"
      [rangesCounts]="rangesCounts | async"
      [(rangeStart)]="rangeStart" [(rangeEnd)]="rangeEnd">
    </gpf-histogram>
  `
})
class TestHostComponentNoDomain {
  public bins = [1, 2, 3, 4];
  public bars = [2, 3, 4, 5];
  public rangeStart = 2;
  public rangeEnd = 4;
  public rangesCounts: Observable<Array<number>> = of([2, 7, 5]);

  @ViewChild('gpfhistogram') public histogramEl;
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
  public bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  public bars = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
  public rangeStart = 2;
  public rangeEnd = 4;
  public domainMin = 1;
  public domainMax = 12;
  public isInteractive = true;
  public rangesCounts: Observable<Array<number>> = of([2, 7, 56]);

  @ViewChild('gpfhistogram') public histogramEl;
}

describe('HistogramComponent', () => {
  let component: TestHostComponent;
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [ FormsModule ],
      declarations: [
        HistogramComponent, HistogramRangeSelectorLineComponent,
        TestHostComponent,
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(TestHostComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render an svg', () => {
    expect(d3.select('svg')).not.toBeNull();
  });

  it('should have the correct width and height', () => {
    expect(d3.select('svg').attr('width')).toBe('650');
    expect(d3.select('svg').attr('height')).toBe('145');
  });

  it('should render the correct amount of bars', waitForAsync(() => {
    fixture.whenStable().then(() => {
      expect(d3.select('svg').selectAll('rect').nodes()).toHaveLength(6);
    });
  }));

  it('should redraw the histogram on changes', waitForAsync(() => {
    jest.spyOn(component.histogramEl, 'redrawHistogram');
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

  it('should render a correct label with the sum of bars within the range', waitForAsync(() => {
    fixture.whenStable().then(() => {
      const sumOfBarsLabelEl = fixture.debugElement.query(By.css('#sumOfBarsLabel'));
      expect(sumOfBarsLabelEl).not.toBeNull();
      expect((sumOfBarsLabelEl.nativeElement as HTMLElement).textContent.trim()).toBe('7 (50.00%)');
    });
  }));

  it('should render sliders', waitForAsync(() => {
    const sliderEls = fixture.debugElement.queryAll(
      el => el.nativeElement.attributes.getNamedItem('gpf-histogram-range-selector-line')
    );
    expect(sliderEls).toHaveLength(2);
  }));

  it('should set the correct labels to the sliders', () => {
    const sliderLabels = fixture.debugElement.queryAll(By.css('.partitions-text'));
    const sliderLabelsText = sliderLabels.map((label) => (label.nativeElement as HTMLElement).textContent.trim());
    expect(sliderLabels).toHaveLength(3);
    expect(sliderLabelsText).toHaveLength(3);
    expect(sliderLabelsText).toStrictEqual(['2 (14.29%)', '5 (35.71%)', '7 (50.00%)']);
  });

  it('should not render range input fields if less than 10 bins', waitForAsync(() => {
    const rangeInputElFrom = fixture.debugElement.query(By.css('.histogram-from'));
    const rangeInputElTo = fixture.debugElement.query(By.css('.histogram-to'));
    expect(rangeInputElFrom).toBeNull();
    expect(rangeInputElTo).toBeNull();
  }));
});

describe('HistogramComponentManyBins', () => {
  let component: TestHostComponentManyBins;
  let fixture: ComponentFixture<TestHostComponentManyBins>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [
        HistogramComponent, HistogramRangeSelectorLineComponent,
        TestHostComponentManyBins,
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(TestHostComponentManyBins);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

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
    expect(rangeInputElFrom.queryAll(By.css('button'))).toHaveLength(2);
    expect(rangeInputElFrom.query(By.css('.step.up'))).not.toBeNull();
    expect(rangeInputElFrom.query(By.css('.step.down'))).not.toBeNull();
    expect(rangeInputElTo.queryAll(By.css('button'))).toHaveLength(2);
    expect(rangeInputElTo.query(By.css('.step.up'))).not.toBeNull();
    expect(rangeInputElTo.query(By.css('.step.down'))).not.toBeNull();
  });
});

describe('HistogramComponentNoDomain', () => {
  let fixture: ComponentFixture<TestHostComponentNoDomain>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [ FormsModule ],
      declarations: [
        HistogramComponent, HistogramRangeSelectorLineComponent,
        TestHostComponentNoDomain,
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(TestHostComponentNoDomain);
    fixture.detectChanges();
  }));

  it('should set the correct labels to the sliders', () => {
    const sliderLabels = fixture.debugElement.queryAll(By.css('.partitions-text'));
    const sliderLabelsText = sliderLabels.map((label) => (label.nativeElement as HTMLElement).textContent.trim());
    expect(sliderLabels).toHaveLength(3);
    expect(sliderLabelsText).toHaveLength(3);
    expect(sliderLabelsText).toStrictEqual(['2 (14.29%)', '5 (35.71%)', '7 (50.00%)']);
  });
});
