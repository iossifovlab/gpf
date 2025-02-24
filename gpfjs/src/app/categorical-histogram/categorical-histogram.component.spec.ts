import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CategoricalHistogramComponent } from './categorical-histogram.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { CategoricalHistogram } from 'app/utils/histogram-types';

describe('CategoricalHistogramComponent', () => {
  let component: CategoricalHistogramComponent;
  let fixture: ComponentFixture<CategoricalHistogramComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [CategoricalHistogramComponent],
      schemas: [NO_ERRORS_SCHEMA],
    })
      .compileComponents();

    fixture = TestBed.createComponent(CategoricalHistogramComponent);
    component = fixture.componentInstance;

    component.histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
      ],
      ['name3', 'name1', 'name2'],
      'large value descriptions',
      'small value descriptions',
      true,
      0
    );

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should init values in correct order', () => {
    component.histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
      ],
      ['name3', 'name1', 'name2'],
      'large value descriptions',
      'small value descriptions',
      true,
      0
    );
    component.initialSelectedValueNames = ['name1', 'name2', 'name3'];

    component.ngOnInit();
    expect(component.values[0].name).toBe('name3');
    expect(component.values[1].name).toBe('name1');
    expect(component.values[2].name).toBe('name2');
  });

  it('should init values with only a certain number of them displayed', () => {
    component.histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
        {name: 'name4', value: 40},
        {name: 'name5', value: 50},
      ],
      ['name1', 'name2', 'name3', 'name4', 'name5'],
      'large value descriptions',
      'small value descriptions',
      true,
      0,
      2,
    );

    component.ngOnInit();
    expect(component.values[0].name).toBe('name1');
    expect(component.values[1].name).toBe('name2');
    expect(component.values[2].name).toBe('Other values');
    expect(component.values[2].value).toBe(120);
  });

  it('should init values with only a percent fraction of them displayed', () => {
    component.histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
        {name: 'name4', value: 40},
        {name: 'name5', value: 50},
      ],
      ['name1', 'name2', 'name3', 'name4', 'name5'],
      'large value descriptions',
      'small value descriptions',
      true,
      0,
      null,
      60,
    );
    fixture.detectChanges();
    component.ngOnInit();
    expect(component.values[0].name).toBe('name1');
    expect(component.values[1].name).toBe('name2');
    expect(component.values[2].name).toBe('name3');
    expect(component.values[3].name).toBe('Other values');
    expect(component.values[3].value).toBe(90);
  });

  it('should sort range values from state for categorical histogram', () => {
    component.initialSelectedValueNames = ['name5', 'name1', 'name3', 'name2', 'name4'];
    component.histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
        {name: 'name4', value: 40},
        {name: 'name5', value: 50},
      ],
      ['name1', 'name2', 'name3', 'name4', 'name5'],
      'large value descriptions',
      'small value descriptions',
      true,
      0,
      3,
    );
    component.interactType = 'range selector';

    component.ngOnInit();
    expect(component.selectedValueNames).toStrictEqual(['name1', 'name2', 'name3', 'Other values']);
  });

  it('should color bars in steelblue with click selector view of categorial historam', () => {
    component.histogram = new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
        {name: 'name4', value: 40},
        {name: 'name5', value: 50},
      ],
      ['name1', 'name2', 'name3', 'name4', 'name5'],
      'large value descriptions',
      'small value descriptions',
      true,
      0,
      2,
    );
    component.initialSelectedValueNames = ['name3', 'name2', 'name1'];
    component.interactType = 'click selector';

    component.ngOnInit();
    expect(component.selectedValueNames).toStrictEqual(['name1', 'name2']);

    let bar: HTMLElement;
    bar = (fixture.nativeElement as HTMLElement).querySelector('rect[id=name1]');
    expect(bar.style.fill).toBe('steelblue');
    bar = (fixture.nativeElement as HTMLElement).querySelector('rect[id=name2]');
    expect(bar.style.fill).toBe('steelblue');

    bar= (fixture.nativeElement as HTMLElement).querySelector('rect[id="Other values"]');
    expect(bar.style.fill).toBe('lightsteelblue');

    bar= (fixture.nativeElement as HTMLElement).querySelector('rect[id=name3]');
    expect(bar).toBeNull();
    bar = (fixture.nativeElement as HTMLElement).querySelector('rect[id=name4]');
    expect(bar).toBeNull();
    bar = (fixture.nativeElement as HTMLElement).querySelector('rect[id=name5]');
    expect(bar).toBeNull();
  });

  it('should check if single score value is valid', () => {
    component.singleScoreValue = 'scoreValue';
    expect(component.singleScoreValueIsValid()).toBe(true);

    component.singleScoreValue = '';
    expect(component.singleScoreValueIsValid()).toBe(false);

    component.singleScoreValue = undefined;
    expect(component.singleScoreValueIsValid()).toBe(false);

    component.singleScoreValue = null;
    expect(component.singleScoreValueIsValid()).toBe(false);
  });

  it('should transform range end slider position into index', () => {
    component.endX = 215;
    expect(component.sliderEndIndex).toBe(1);

    component.endX = 50;
    expect(component.sliderEndIndex).toBe(0);

    component.sliderStartIndex = 2;
    component.endX = 215;
    expect(component.sliderEndIndex).toBe(0);

    component.sliderStartIndex = 0;
    component.sliderEndIndex = 1;
    component.endX = 215;
    expect(component.sliderEndIndex).toBe(1);
  });

  it('should transform range start slider position into index', () => {
    component.startX = 215;
    expect(component.sliderStartIndex).toBe(2);

    component.startX = 50;
    expect(component.sliderStartIndex).toBe(0);

    component.sliderEndIndex = 1;
    component.startX = 215;
    expect(component.sliderStartIndex).toBe(0);

    component.sliderStartIndex = 0;
    component.sliderEndIndex = 1;
    component.startX = 215;
    expect(component.sliderStartIndex).toBe(0);
  });

  it('should redraw histogram when changes are detected', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const redrawHistogramSpy = jest.spyOn(component as any, 'redrawHistogram');
    component.ngOnChanges();
    expect(redrawHistogramSpy).toHaveBeenCalledWith();
  });
});
