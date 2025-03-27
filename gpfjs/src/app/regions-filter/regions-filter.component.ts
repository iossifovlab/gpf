import { RegionsFilter } from './regions-filter';
import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectRegionsFilters, setRegionsFilters } from './regions-filter.state';
import { ValidateNested } from 'class-validator';
import { ComponentValidator } from 'app/common/component-validator';
import { take } from 'rxjs';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
})
export class RegionsFilterComponent extends ComponentValidator implements OnInit {
  @Input() public genome: string;
  @ValidateNested() public regionsFilter = new RegionsFilter();
  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(
    protected store: Store,
  ) {
    super(store, 'regionsFilter', selectRegionsFilters);
  }

  public ngOnInit(): void {
    this.store.select(selectRegionsFilters).pipe(take(1))
      .subscribe((regionsFilters: string[]) => {
        this.focusTextInputArea();
        this.regionsFilter.genome = this.genome;
        super.ngOnInit();
        this.setRegionsFilter(regionsFilters.join('\n'));
      });
  }

  public setRegionsFilter(regionsFilter: string): void {
    const result = regionsFilter
      .split(/[\s]/)
      .map(s => s.replace(/[,]/g, ''))
      .filter(s => s !== '');
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
      this.textArea.nativeElement.focus();
    });
  }
}
