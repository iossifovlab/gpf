import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetGeneSymbols, GeneSymbolsState } from './gene-symbols.state';
import { StatefulComponent } from 'app/common/stateful-component';

export class GeneSymbols {
  @IsNotEmpty()
  public geneSymbols = '';
}

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent extends StatefulComponent implements OnInit {

  @ValidateNested()
  public geneSymbols: GeneSymbols = new GeneSymbols();

  @ViewChild('textArea') private textArea: ElementRef;

  constructor(protected store: Store) {
    super(store, GeneSymbolsState, 'geneSymbols');
  }

  public ngOnInit() {
    super.ngOnInit();
    this.focusGeneTextArea();
    this.store.selectOnce(GeneSymbolsState).subscribe(state => {
      // restore state
      this.setGeneSymbols(state.geneSymbols.join('\n'));
    });
  }

  public setGeneSymbols(geneSymbols: string) {
    const result = geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '')
      .map(s => s.toUpperCase());
    this.geneSymbols.geneSymbols = geneSymbols;
    this.store.dispatch(new SetGeneSymbols(result));
  }

  /**
  * Waits gene text area element to load.
  * @returns promise
  */
  private async waitForGeneTextAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.textArea !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 200);
    });
  }

  private focusGeneTextArea() {
    this.waitForGeneTextAreaToLoad().then(() => {
      this.textArea.nativeElement.focus();
    });
  }
}
