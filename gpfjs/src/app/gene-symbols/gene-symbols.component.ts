import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectGeneSymbols, setGeneSymbols } from './gene-symbols.state';
import { BehaviorSubject, debounceTime, distinctUntilChanged, take } from 'rxjs';
import { GeneService } from 'app/gene-browser/gene.service';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent implements OnInit {
  public geneSymbols: string = '';
  public invalidGenes: string;
  public geneSymbolsInput$: BehaviorSubject<string> = new BehaviorSubject<string>('');
  public errors: string[] = [];

  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store, private geneService: GeneService) { }

  public ngOnInit(): void {
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
      this.errors = [];
      this.geneSymbols = '';
      this.invalidGenes = '';
      return;
    }

    const genes = geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.geneSymbols = geneSymbols;

    this.validateState(genes);
  }

  private validateState(genes: string[]): void {
    this.geneService.validateGenes(genes).subscribe(invalidGenes => {
      this.errors = [];
      this.invalidGenes = '';

      if (!invalidGenes.length) {
        this.store.dispatch(resetErrors({componentId: 'geneSymbols'}));
        this.store.dispatch(setGeneSymbols({geneSymbols: genes}));
      } else {
        this.invalidGenes = invalidGenes.join(', ');
        this.errors.push(`Invalid genes: ${this.invalidGenes}`);

        this.store.dispatch(setErrors({
          errors: {
            componentId: 'geneSymbols', errors: cloneDeep(this.errors)
          }
        }));
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
