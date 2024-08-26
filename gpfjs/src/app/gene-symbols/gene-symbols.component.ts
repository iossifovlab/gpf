import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { Store } from '@ngrx/store';
import { selectGeneSymbols, setGeneSymbols } from './gene-symbols.state';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { take } from 'rxjs';

export class GeneSymbols {
  @IsNotEmpty()
  public geneSymbols = '';
}

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent extends StatefulComponentNgRx implements OnInit {
  @ValidateNested()
  public geneSymbols: GeneSymbols = new GeneSymbols();

  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store) {
    super(store, 'geneSymbols', selectGeneSymbols);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.focusGeneTextArea();
    this.store.select(selectGeneSymbols).pipe(take(1)).subscribe(geneSymbolsState => {
      // restore state
      let separator = '\n';
      if (geneSymbolsState.length >= 3) {
        separator = ', ';
      }
      this.setGeneSymbols(geneSymbolsState.join(separator));
    });
  }

  public setGeneSymbols(geneSymbols: string): void {
    const result = geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.geneSymbols.geneSymbols = geneSymbols;
    this.store.dispatch(setGeneSymbols({geneSymbols: result}));
  }

  /**
   * Waits gene text area element to load.
   *
   * @returns promise
   */
  private async waitForGeneTextAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.textArea !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  private focusGeneTextArea(): void {
    this.waitForGeneTextAreaToLoad().then(() => {
      (this.textArea.nativeElement as HTMLElement).focus();
    });
  }
}
