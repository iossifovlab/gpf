import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { Store } from '@ngrx/store';
import { selectGeneSymbols, setGeneSymbols } from './gene-symbols.state';
import { ComponentValidator } from 'app/common/component-validator';
import { BehaviorSubject, debounceTime, distinctUntilChanged, take } from 'rxjs';
import { GeneService } from 'app/gene-browser/gene.service';

export class GeneSymbols {
  @IsNotEmpty()
  public geneSymbols = '';
}

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent extends ComponentValidator implements OnInit {
  @ValidateNested()
  public geneSymbols: GeneSymbols = new GeneSymbols();
  public invalidGenes: string;
  public geneSymbolsInput$: BehaviorSubject<string> = new BehaviorSubject<string>('');

  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store, private geneService: GeneService) {
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
      this.geneSymbolsInput$.next(geneSymbolsState.join(separator));
    });

    this.geneSymbolsInput$.pipe(
      distinctUntilChanged(),
      debounceTime(350),
    ).subscribe(genes => {
      this.setGeneSymbols(genes);
    });
  }

  public setGeneSymbols(geneSymbols: string): void {
    if (!geneSymbols) {
      this.geneSymbols.geneSymbols = '';
      this.invalidGenes = '';
      return;
    }

    const result = geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.geneSymbols.geneSymbols = geneSymbols;

    this.geneService.validateGenes(result).subscribe(invalidGenes => {
      this.invalidGenes = '';
      if (!invalidGenes.length) {
        this.store.dispatch(setGeneSymbols({geneSymbols: result}));
      } else {
        this.invalidGenes = invalidGenes.join(', ');
      }
    });
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
