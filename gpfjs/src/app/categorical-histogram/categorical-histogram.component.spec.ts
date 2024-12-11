import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CategoricalHistogramComponent } from './categorical-histogram.component';
import { CategoricalHistogram } from 'app/gene-scores/gene-scores';

describe('CategoricalHistogramComponent', () => {
  let component: CategoricalHistogramComponent;
  let fixture: ComponentFixture<CategoricalHistogramComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [CategoricalHistogramComponent]
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
    );

    component.ngOnInit();
    expect(component.histogram.values[0].name).toBe('name3');
    expect(component.histogram.values[1].name).toBe('name1');
    expect(component.histogram.values[2].name).toBe('name2');
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
      2,
    );

    component.ngOnInit();
    expect(component.histogram.values[0].name).toBe('name1');
    expect(component.histogram.values[1].name).toBe('name2');
    expect(component.histogram.values[2].name).toBe('other');
    expect(component.histogram.values[2].value).toBe(120);
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
      null,
      60,
    );

    component.ngOnInit();
    expect(component.histogram.values[0].name).toBe('name1');
    expect(component.histogram.values[1].name).toBe('name2');
    expect(component.histogram.values[2].name).toBe('name3');
    expect(component.histogram.values[3].name).toBe('other');
    expect(component.histogram.values[3].value).toBe(90);
  });

  it('should sort range values from state for categorical histogram', () => {
    component.stateCategoricalNames = ['name5', 'name1', 'name3', 'name2', 'name4'];
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
      2,
    );
    component.interactType = 'range selector';

    component.ngOnInit();
    expect(component.stateCategoricalNames).toStrictEqual(['name1', 'name2', 'name3', 'name4', 'name5']);
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
      2,
    );
    component.stateCategoricalNames = ['name3', 'name1'];
    component.interactType = 'click selector';

    component.ngOnInit();
    expect(component.stateCategoricalNames).toStrictEqual(['name3', 'name1']);

    const notSelectedBar: HTMLElement = (fixture.nativeElement as HTMLElement).querySelector('rect[id=name2]');
    expect(notSelectedBar.style.fill).toBe('lightsteelblue');

    const selectedBar: HTMLElement = (fixture.nativeElement as HTMLElement).querySelector('rect[id=name1]');
    expect(selectedBar.style.fill).toBe('steelblue');
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
