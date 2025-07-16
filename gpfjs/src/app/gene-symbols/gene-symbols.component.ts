import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectGeneSymbols, setGeneSymbols } from './gene-symbols.state';
import { Subscription, take } from 'rxjs';
import { GeneService } from 'app/gene-browser/gene.service';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
    selector: 'gpf-gene-symbols',
    templateUrl: './gene-symbols.component.html',
    standalone: false
})
export class GeneSymbolsComponent implements OnInit, OnDestroy {
  public geneSymbols: string = '';
  public invalidGenes: string;
  public errors: string[] = [];
  private validationSubscription = new Subscription();

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
      this.geneSymbols = geneSymbolsState.join(separator);
      this.validateState(geneSymbolsState);
    });
  }

  public setGeneSymbols(geneSymbols: string): void {
    geneSymbols = geneSymbols.trim();
    if (!geneSymbols) {
      this.geneSymbols = '';
      this.validateState([]);
      this.store.dispatch(setGeneSymbols({geneSymbols: []}));
      return;
    }

    const genes = geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.geneSymbols = geneSymbols;

    this.validateState(genes);
    this.store.dispatch(setGeneSymbols({geneSymbols: genes}));
  }

  private validateState(genes: string[]): void {
    if (!genes.length) {
      this.errors = [];
      this.invalidGenes = '';
      this.errors.push('Please insert at least one gene symbol.');
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'geneSymbols', errors: cloneDeep(this.errors)
        }
      }));
      return;
    }

    this.validationSubscription.unsubscribe();

    this.validationSubscription = this.geneService.validateGenes(genes).subscribe(invalidGenes => {
      this.errors = [];
      this.invalidGenes = '';

      if (!invalidGenes.length) {
        this.store.dispatch(resetErrors({componentId: 'geneSymbols'}));
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

  public ngOnDestroy(): void {
    this.store.dispatch(resetErrors({componentId: 'geneSymbols'}));
  }
}
