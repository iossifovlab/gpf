import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CategoricalValuesDropdownComponent } from './categorical-values-dropdown.component';
import { MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { CategoricalHistogram } from 'app/genomic-scores-block/genomic-scores-block';

describe('CategoricalValuesDropdownComponent', () => {
  let component: CategoricalValuesDropdownComponent;
  let fixture: ComponentFixture<CategoricalValuesDropdownComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [CategoricalValuesDropdownComponent],
      imports: [
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CategoricalValuesDropdownComponent);
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
});
