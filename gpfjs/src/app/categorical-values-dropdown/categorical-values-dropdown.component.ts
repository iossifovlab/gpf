import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CategoricalHistogram } from 'app/utils/histogram-types';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'gpf-categorical-values-dropdown',
  templateUrl: './categorical-values-dropdown.component.html',
  styleUrl: './categorical-values-dropdown.component.css'
})
export class CategoricalValuesDropdownComponent implements OnInit {
  @Input() public initialState: string[] = [];
  @Input() public histogram: CategoricalHistogram;
  @Output() public updateSelectedValues = new EventEmitter<string[]>();
  public valueSuggestions = [];
  public searchValue = '';
  public searchBoxInput$: Subject<string> = new Subject();
  public categoricalValues: { name: string; value: number; }[] = [];
  public selectedValues: { name: string; value: number; }[] = [];
  private suggestionsToShow = 50;

  public errors: string[] = [];
  @Output() public emitValidationErrors = new EventEmitter<string[]>();

  public ngOnInit(): void {
    this.categoricalValues = this.histogram.values;
    this.valueSuggestions = this.categoricalValues.slice(0, this.suggestionsToShow);

    if (this.initialState.length) {
      this.selectedValues = this.histogram.values.filter(v => this.initialState.includes(v.name));
    }
    this.validateState();

    this.searchBoxInput$.pipe(debounceTime(100), distinctUntilChanged()).subscribe(() => {
      if (!this.searchValue) {
        this.valueSuggestions = this.categoricalValues.slice(0, this.suggestionsToShow);
        return;
      }
      this.filterSuggestions();
    });
  }

  public filterSuggestions(): void {
    this.valueSuggestions = this.categoricalValues.filter(value => {
      const valueLowerCase = value.name.toLowerCase();
      const searchValueLowerCase = this.searchValue.toLowerCase();
      return valueLowerCase.startsWith(searchValueLowerCase);
    }).slice(0, this.suggestionsToShow);
  }

  public addToSelected(value: { name: string; value: number; }): void {
    if (!this.selectedValues.find(v => v.name === value.name)) {
      this.selectedValues.push(value);
      this.updateSelectedValues.emit(this.selectedValues.map(v => v.name));
    }
    this.searchValue = '';
    this.searchBoxInput$.next(this.searchValue);

    this.validateState();
  }

  public removeFromSelected(value: string): void {
    const index = this.selectedValues.findIndex(v => v.name === value);
    if (index > -1) {
      this.selectedValues.splice(index, 1);
      this.updateSelectedValues.emit(this.selectedValues.map(v => v.name));
    }

    this.validateState();
  }

  public isSelected(suggestion: { name: string; value: number; }): boolean {
    return Boolean(this.selectedValues.find(v => v.name === suggestion.name));
  }

  private validateState(): void {
    this.errors = [];

    if (!this.selectedValues.length) {
      this.errors.push('Please select at least one value.');
    }

    this.emitValidationErrors.emit(this.errors);
  }
}
