import { RegionsFilter } from './regions-filter';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngxs/store';
import { RegionsFilterState, SetRegionsFilter } from './regions-filter.state';
import { ValidateNested } from 'class-validator';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
})
export class RegionsFilterComponent extends StatefulComponent implements OnInit {
  @ValidateNested()
  regionsFilter = new RegionsFilter();

  constructor(protected store: Store) {
    super(store, RegionsFilterState, 'regionsFilter');
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(state => state.regionsFiltersState).subscribe(state => {
      this.setRegionsFilter(state.regionsFilters.join('\n'));
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
