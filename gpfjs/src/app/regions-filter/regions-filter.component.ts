import { RegionsFilter } from './regions-filter';
import { Component, ElementRef, Input, OnInit, ViewChild, OnDestroy } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectRegionsFilters, setRegionsFilters } from './regions-filter.state';
import { take } from 'rxjs';
import { cloneDeep } from 'lodash';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
})
export class RegionsFilterComponent implements OnInit, OnDestroy {
  @Input() public genome: string;
  public regionsFilter = new RegionsFilter();
  public errors: string[] = [];

  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(
    protected store: Store,
  ) {}

  public ngOnInit(): void {
    this.store.select(selectRegionsFilters).pipe(take(1))
      .subscribe((regionsFilters: string[]) => {
        this.focusTextInputArea();
        this.regionsFilter.genome = this.genome;
        this.validateState(regionsFilters);
        this.regionsFilter.regionsFilter = regionsFilters.join('\n');
      });
  }

  public setRegionsFilter(regionsFilter: string): void {
    let formattedFilter = regionsFilter + '\n';
    formattedFilter = formattedFilter.replace(/,(?![0-9]{3}\D{1})/g, '\n');
    const result = formattedFilter
      .split('\n')
      .map(t => t.trim())
      .filter(s => s !== '');
    this.validateState(result);
    this.regionsFilter.regionsFilter = regionsFilter;
    this.store.dispatch(setRegionsFilters({regionsFilter: cloneDeep(result)}));
  }

  private async waitForTextInputAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.textArea !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  private focusTextInputArea(): void {
    this.waitForTextInputAreaToLoad().then(() => {
      (this.textArea.nativeElement as HTMLTextAreaElement).focus();
    });
  }

  private validateState(state: string[]): void {
    this.errors = [];

    if (state.length === 0) {
      this.errors.push('Add at least one region filter.');
    } else {
      for (const region of state) {
        if (!this.isRegionValid(region, this.genome)) {
          this.errors.push(`Invalid region: ${region}`);
        }
      }
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'regionsFilter', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'regionsFilter'}));
    }
  }

  private isRegionValid(region: string, genome: string): boolean {
    region = region.replaceAll(',', '');
    let chromRegex = '(2[0-2]|1[0-9]|[0-9]|X|Y)';
    if (genome === 'hg38') {
      chromRegex = 'chr' + chromRegex;
    }
    const lineRegex = `${chromRegex}:([0-9]+)(?:-([0-9]+))?|${chromRegex}`;
    const match = region.match(new RegExp(lineRegex, 'i'));
    if (match === null || match[0] !== region) {
      return false;
    }

    if (
      match.length >= 3
      && match[2]
      && match[3]
      && Number(match[2].replace(',', '')) > Number(match[3].replace(',', ''))
    ) {
      return false;
    }

    return true;
  }

  public ngOnDestroy(): void {
    this.store.dispatch(resetErrors({componentId: 'regionsFilter'}));
  }
}
