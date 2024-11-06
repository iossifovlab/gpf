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
});
