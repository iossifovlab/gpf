import { Component, Input, OnInit } from '@angular/core';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'gpf-categorical-values-dropdown',
  templateUrl: './categorical-values-dropdown.component.html',
  styleUrl: './categorical-values-dropdown.component.css'
})
export class CategoricalValuesDropdownComponent implements OnInit {
  @Input() public categoricalValues: string[] = [];
  public valueSuggestions = [];
  public searchCategoricalValue = '';
  public selectedValues: string[] = [];
  public searchBoxInput$: Subject<string> = new Subject();

  public ngOnInit(): void {
    this.valueSuggestions = this.categoricalValues.slice(0, 10);

    this.searchBoxInput$.pipe(debounceTime(100), distinctUntilChanged()).subscribe(() => {
      if (!this.searchCategoricalValue) {
        this.valueSuggestions = this.categoricalValues.slice(0, 10);
        return;
      }
      this.filterSuggestions();
    });
  }

  public filterSuggestions(): void {
    this.valueSuggestions = this.categoricalValues.filter(value => {
      value = value.toLowerCase();
      const searchValueLowerCase = this.searchCategoricalValue.toLowerCase();
      return value.startsWith(searchValueLowerCase);
    }).slice(0, 10);
  }

  public selectCategoricalValue(value :string): void {
    if (!this.selectedValues.includes(value)) {
      this.selectedValues.push(value);
    }
    this.searchCategoricalValue = '';
  }

  public removeFromSelected(value: string): void {
    const index = this.selectedValues.indexOf(value);
    if (index > -1) {
      this.selectedValues.splice(index, 1);
    }
  }
}
