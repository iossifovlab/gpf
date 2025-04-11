import { Component, Input, OnInit } from '@angular/core';
import { resetZygosityFilter, selectZygosityFilter, setZygosityFilter } from './zygosity-filter.state';
import { Store } from '@ngrx/store';
import { take } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
  selector: 'gpf-zygosity-filter',
  templateUrl: './zygosity-filter.component.html',
  styleUrl: './zygosity-filter.component.css'
})
export class ZygosityFilterComponent implements OnInit {
  @Input() public parentComponent: string;
  public zygosityTypes: string[] = [];
  public selectedZygosityTypes: Set<string> = new Set<string>();

  public constructor(private store: Store) {}

  public ngOnInit(): void {
    this.zygosityTypes = ['homozygous', 'heterozygous'];

    this.store.select(selectZygosityFilter).pipe(take(1)).subscribe(zygosityFilter => {
      if (zygosityFilter?.length) {
        const filterFromState = zygosityFilter.find(z => z.componentId === this.parentComponent).filter;
        this.selectedZygosityTypes.add(filterFromState);
      } else {
        this.selectedZygosityTypes.add(this.zygosityTypes[0]);
        this.selectedZygosityTypes.add(this.zygosityTypes[1]);
      }
    });
  }

  public checkZygosityType(zygosityType: string, value: boolean): void {
    if (value) {
      this.selectedZygosityTypes.add(zygosityType);
    } else {
      this.selectedZygosityTypes.delete(zygosityType);
    }
    if (this.selectedZygosityTypes.size === this.zygosityTypes.length) {
      this.store.dispatch(resetZygosityFilter({componentId: this.parentComponent}));
    } else {
      this.store.dispatch(setZygosityFilter({zygosityFilter: {
        componentId: this.parentComponent,
        filter: [...this.selectedZygosityTypes][0]
      }}));
    }
    this.validateState();
  }

  public validateState(): void {
    if (!this.selectedZygosityTypes.size) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: `zygosityFilter: ${this.parentComponent}`, errors: ['Select at least one zygosity.']
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: `zygosityFilter: ${this.parentComponent}`}));
    }
  }
}
