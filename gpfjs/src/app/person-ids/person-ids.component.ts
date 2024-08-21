import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { Store } from '@ngrx/store';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { selectPersonIds, setPersonIds } from './person-ids.state';
import { take } from 'rxjs';

export class PersonIds {
  @IsNotEmpty({message: 'Please insert at least one person id.'})
  public personIds = '';
}

@Component({
  selector: 'gpf-person-ids',
  templateUrl: './person-ids.component.html',
  styleUrls: ['./person-ids.component.css'],
})
export class PersonIdsComponent extends StatefulComponentNgRx implements OnInit {
  @ValidateNested()
  public personIds = new PersonIds();
  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store) {
    super(store, 'personIds', selectPersonIds);
  }

  public ngOnInit(): void {
    super.ngOnInit();
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
    const result = personIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.personIds.personIds = personIds;
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
      this.textArea.nativeElement.focus();
    });
  }
}
