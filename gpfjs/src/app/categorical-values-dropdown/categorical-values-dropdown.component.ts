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
  @Input() public histogram: CategoricalHistogram;
  @Output() public updateSelectedValues = new EventEmitter<string[]>();
  public valueSuggestions = [];
  public searchValue = '';
  public searchBoxInput$: Subject<string> = new Subject();
  public categoricalValues: { name: string; value: number; }[] = [];
  public selectedValues: { name: string; value: number; }[] = [];

  public ngOnInit(): void {
    this.categoricalValues = this.histogram.values;
    this.valueSuggestions = this.categoricalValues.slice(0, 10);

    if (this.initialState.length) {
      this.selectedValues = this.histogram.values.filter(v => this.initialState.includes(v.name));
    }

    this.searchBoxInput$.pipe(debounceTime(100), distinctUntilChanged()).subscribe(() => {
      if (this.searchValue === '') {
        this.valueSuggestions = this.categoricalValues.slice(0, 10);
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
    }).slice(0, 10);
  }

  public addToSelected(value: { name: string; value: number; }): void {
    if (!this.selectedValues.includes(value)) {
      this.selectedValues.push(value);
      this.updateSelectedValues.emit(this.selectedValues.map(v => v.name));
    }
    this.searchValue = '';
    this.searchBoxInput$.next(this.searchValue);
  }

  public removeFromSelected(value: string): void {
    const index = this.selectedValues.findIndex(v => v.name === value);
    if (index > -1) {
      this.selectedValues.splice(index, 1);
      this.updateSelectedValues.emit(this.selectedValues.map(v => v.name));
    }
  }

  public isSelected(suggestion: { name: string; value: number; }): boolean {
    return this.selectedValues.includes(suggestion);
  }
}
