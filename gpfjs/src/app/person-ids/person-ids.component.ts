import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectPersonIds, setPersonIds } from './person-ids.state';
import { take } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';


@Component({
  selector: 'gpf-person-ids',
  templateUrl: './person-ids.component.html',
  styleUrls: ['./person-ids.component.css'],
})
export class PersonIdsComponent implements OnInit {
  public personIds = '';
  public errors: string[] = [];
  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store) { }

  public ngOnInit(): void {
    this.focusTextInputArea();

    this.store.select(selectPersonIds).pipe(take(1)).subscribe((personIds: string[]) => {
      let separator = '\n';
      if (personIds.length >= 3) {
        separator = ', ';
      }
      this.setPersonIds(personIds.join(separator));
    });
  }

  public setPersonIds(personIds: string): void {
    this.validateState(personIds);

    const result = personIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.personIds = personIds;

    this.store.dispatch(setPersonIds({personIds: result}));
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

  private validateState(personIds: string): void {
    this.errors = [];
    if (!personIds) {
      this.errors.push('Please insert at least one person id.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'personIds', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'personIds'}));
    }
  }
}
