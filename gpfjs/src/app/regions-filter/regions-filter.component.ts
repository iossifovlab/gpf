import { RegionsFilter } from './regions-filter';
import { Component, OnInit } from '@angular/core';
import { Select, Store } from '@ngxs/store';
import { Observable } from 'rxjs';
import { RegionsFilterModel, RegionsFilterState, SetRegionsFilter } from './regions-filter.state';
import { validate } from 'class-validator';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
})
export class RegionsFilterComponent implements OnInit {
  regionsFilter = new RegionsFilter();
  errors: string[] = [];

  @Select(RegionsFilterState) state$: Observable<RegionsFilterModel>;

  constructor(private store: Store) { }

  ngOnInit() {
    this.store.selectOnce(state => state.regionsFiltersState).subscribe(state => {
      console.log(state);
      this.regionsFilter.regionsFilter = state.regionsFilters.join('\n');
    });

    this.state$.subscribe(() => {
      validate(this.regionsFilter).then(errors => { this.errors = errors.map(err => String(err)); });
    });
  }

  setRegionsFilter(regionsFilter: string) {
    const result = regionsFilter
      .split(/[\s]/)
      .map(s => s.replace(/[,]/g, ''))
      .filter(s => s !== '');
    this.regionsFilter.regionsFilter = regionsFilter;
    this.store.dispatch(new SetRegionsFilter(result));
  }
}
