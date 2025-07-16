import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectFamilyIds, setFamilyIds } from './family-ids.state';
import { take } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
    selector: 'gpf-family-ids',
    templateUrl: './family-ids.component.html',
    standalone: false
})
export class FamilyIdsComponent implements OnInit, OnDestroy {
  public familyIds = '';
  @ViewChild('textArea') private textArea: ElementRef;
  public errors: string[] = [];

  public constructor(protected store: Store) {}

  public ngOnInit(): void {
    this.focusTextInputArea();
    this.store.select(selectFamilyIds).pipe(take(1)).subscribe((familyIds: string[]) => {
      if (familyIds.length) {
        // restore state
        this.familyIds = familyIds.join('\n'); // must join on more conditions most likely
      } else {
        this.validateState('');
      }
    });
  }

  public setFamilyIds(familyIds: string): void {
    this.validateState(familyIds);

    const result = familyIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.familyIds = familyIds;
    this.store.dispatch(setFamilyIds({familyIds: result}));
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
      (this.textArea.nativeElement as HTMLElement).focus();
    });
  }

  private validateState(familyIds: string): void {
    this.errors = [];
    if (!familyIds) {
      this.errors.push('Please insert at least one family id.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'familyIds', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'familyIds'}));
    }
  }

  public ngOnDestroy(): void {
    this.store.dispatch(resetErrors({componentId: 'familyIds'}));
  }
}
