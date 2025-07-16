import { Component, Input, OnInit } from '@angular/core';
import { resetZygosityFilter, selectZygosityFilter, setZygosityFilter } from './zygosity-filter.state';
import { Store } from '@ngrx/store';
import { take } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
    selector: 'gpf-zygosity-filter',
    templateUrl: './zygosity-filter.component.html',
    styleUrl: './zygosity-filter.component.css',
    standalone: false
})
export class ZygosityFilterComponent implements OnInit {
  @Input() public parentComponent: string;
  public zygosityTypes: string[] = [];
  public selectedZygosityTypes: Set<string> = new Set<string>();

  public constructor(private store: Store) {}

  public ngOnInit(): void {
    this.zygosityTypes = ['homozygous', 'heterozygous'];

    this.store.select(selectZygosityFilter).pipe(take(1)).subscribe(zygosityFilter => {
      let checkAll = true;
      if (zygosityFilter?.length) {
        const componentZygosity = zygosityFilter.find(z => z.componentId === this.parentComponent);
        if (componentZygosity) {
          checkAll = false;
          const filterFromState = componentZygosity.filter;
          this.selectedZygosityTypes.add(filterFromState);
        }
      }

      if (checkAll) {
        this.selectedZygosityTypes.add(this.zygosityTypes[0]);
        this.selectedZygosityTypes.add(this.zygosityTypes[1]);
      }
    });
  }

  public checkZygosityType(zygosityType: string, isChecked: boolean): void {
    if (isChecked) {
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
