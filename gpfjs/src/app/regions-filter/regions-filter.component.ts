import { RegionsFilter } from './regions-filter';
import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { Store } from '@ngxs/store';
import { RegionsFilterModel, RegionsFilterState, SetRegionsFilter } from './regions-filter.state';
import { ValidateNested } from 'class-validator';
import { StatefulComponent } from 'app/common/stateful-component';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
})
export class RegionsFilterComponent extends StatefulComponent implements OnInit {
  @Input() public genome = '';
  @ValidateNested() public regionsFilter = new RegionsFilter();
  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store, private datsetsService: DatasetsService) {
    super(store, RegionsFilterState, 'regionsFilter');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.focusTextInputArea();
    this.regionsFilter.genome = this.genome;
    this.store.selectOnce((state: { regionsFiltersState: RegionsFilterModel}) => state.regionsFiltersState)
      .subscribe(state => {
        this.setRegionsFilter(state.regionsFilters.join('\n'));
      });
  }

  public setRegionsFilter(regionsFilter: string): void {
    const result = regionsFilter
      .split(/[\s]/)
      .map(s => s.replace(/[,]/g, ''))
      .filter(s => s !== '');
    this.regionsFilter.regionsFilter = regionsFilter;
    this.store.dispatch(new SetRegionsFilter(result));
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
