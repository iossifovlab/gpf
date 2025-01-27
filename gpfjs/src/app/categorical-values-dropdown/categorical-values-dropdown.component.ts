import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CategoricalHistogram } from 'app/genomic-scores-block/genomic-scores-block';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'gpf-categorical-values-dropdown',
  templateUrl: './categorical-values-dropdown.component.html',
  styleUrl: './categorical-values-dropdown.component.css'
})
export class CategoricalValuesDropdownComponent implements OnInit {
  @Input() public initialState: string[] = [];
  public valueSuggestions = [];
  public searchValue = '';
  public selectedValues: string[] = [];
  public searchBoxInput$: Subject<string> = new Subject();
  @Output() public updateSelectedValues = new EventEmitter<string[]>();
  @Input() public histogram: CategoricalHistogram;
  public categoricalValueNames: string[] = [];

  public ngOnInit(): void {
    this.categoricalValueNames = this.histogram.values.map(v => v.name);
    this.valueSuggestions = this.categoricalValueNames.slice(0, 10);

    this.searchBoxInput$.pipe(debounceTime(100), distinctUntilChanged()).subscribe(() => {
      if (this.searchValue === '') {
        this.valueSuggestions = this.categoricalValueNames.slice(0, 10);
        return;
      }
      this.filterSuggestions();
    });
  }

  public filterSuggestions(): void {
    this.valueSuggestions = this.categoricalValueNames.filter(value => {
      value = value.toLowerCase();
      const searchValueLowerCase = this.searchValue.toLowerCase();
      return value.startsWith(searchValueLowerCase);
    }).slice(0, 10);
  }

  public addToSelected(value :string): void {
    if (!this.selectedValues.includes(value)) {
      this.selectedValues.push(value);
      this.updateSelectedValues.emit(this.selectedValues);
    }
    this.searchValue = '';
    this.searchBoxInput$.next(this.searchValue);
  }

  public removeFromSelected(value: string): void {
    const index = this.selectedValues.indexOf(value);
    if (index > -1) {
      this.selectedValues.splice(index, 1);
      this.updateSelectedValues.emit(this.selectedValues);
    }
  }

  public isSelected(suggestion: string): boolean {
    return this.selectedValues.includes(suggestion);
  }
}
