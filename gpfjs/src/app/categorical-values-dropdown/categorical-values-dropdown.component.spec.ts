import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { CategoricalValuesDropdownComponent } from './categorical-values-dropdown.component';
import { MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { CategoricalHistogram } from 'app/genomic-scores-block/genomic-scores-block';
import { NO_ERRORS_SCHEMA } from '@angular/core';

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
      ],
      schemas: [NO_ERRORS_SCHEMA]
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

  it('should set selected values from state', () => {
    component.initialState = ['name2'];
    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual([{name: 'name2', value: 20}]);
  });

  it('should trigger filtering dropdown values when searching', fakeAsync(() => {
    const filterSpy = jest.spyOn(component, 'filterSuggestions');
    const mockSearchValue = '2';
    component.searchValue = mockSearchValue;

    component.searchBoxInput$.next(mockSearchValue);
    tick(100);
    expect(filterSpy).toHaveBeenCalledWith();
  }));

  it('should fill dropdown with default values', fakeAsync(() => {
    const filterSpy = jest.spyOn(component, 'filterSuggestions');
    const mockSearchValue = '';
    component.searchValue = mockSearchValue;
    component['suggestionsToShow'] = 2;

    component.searchBoxInput$.next(mockSearchValue);
    tick(100);
    expect(component.valueSuggestions).toStrictEqual([
      {name: 'name1', value: 10},
      {name: 'name2', value: 20}
    ]);
    expect(filterSpy).not.toHaveBeenCalledWith();
  }));

  it('should filter categorical values suggestions in dropdown', () => {
    component.searchValue = 'nAMe3';
    component.filterSuggestions();
    expect(component.valueSuggestions).toStrictEqual([{name: 'name3', value: 30}]);
  });

  it('should select categorical value from dropdown', () => {
    const emitSpy = jest.spyOn(component.updateSelectedValues, 'emit');
    component.searchValue = '3';
    component.selectedValues = [{name: 'name2', value: 20}];
    component.addToSelected({name: 'name3', value: 30});
    expect(component.selectedValues).toStrictEqual([
      {name: 'name2', value: 20},
      {name: 'name3', value: 30}
    ]);
    expect(component.searchValue).toBe('');
    expect(emitSpy).toHaveBeenCalledWith(['name2', 'name3']);
  });

  it('should not add already selected categorical value from dropdown', () => {
    const emitSpy = jest.spyOn(component.updateSelectedValues, 'emit');
    component.searchValue = '3';
    component.selectedValues = [{name: 'name2', value: 20}, {name: 'name3', value: 30}];
    component.addToSelected({name: 'name3', value: 30});
    expect(component.selectedValues).toStrictEqual([
      {name: 'name2', value: 20},
      {name: 'name3', value: 30}
    ]);
    expect(component.searchValue).toBe('');
    expect(emitSpy).not.toHaveBeenCalledWith();
  });

  it('should remove categorical value from list of values', () => {
    const emitSpy = jest.spyOn(component.updateSelectedValues, 'emit');
    component.selectedValues = [{name: 'name2', value: 20}, {name: 'name3', value: 30}];
    component.removeFromSelected('name2');
    expect(component.selectedValues).toStrictEqual([
      {name: 'name3', value: 30}
    ]);
    expect(component.searchValue).toBe('');
    expect(emitSpy).toHaveBeenCalledWith(['name3']);
  });

  it('should check is a value is selected', () => {
    component.selectedValues = [{name: 'name3', value: 30}];
    expect(component.isSelected({name: 'name3', value: 30})).toBe(true);
    expect(component.isSelected({name: 'name2', value: 20})).toBe(false);
  });
});
