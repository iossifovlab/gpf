import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetPersonIds, PersonIdsState } from './person-ids.state';
import { StatefulComponent } from 'app/common/stateful-component';

export class PersonIds {
  @IsNotEmpty({message: 'Please insert at least one person id.'})
  personIds = '';
}

@Component({
  selector: 'gpf-person-ids',
  templateUrl: './person-ids.component.html',
  styleUrls: ['./person-ids.component.css'],
})
export class PersonIdsComponent extends StatefulComponent implements OnInit {
  @ValidateNested()
  personIds = new PersonIds();
  @ViewChild('textArea') private textArea: ElementRef;

  constructor(protected store: Store) {
    super(store, PersonIdsState, 'personIds')
  }

  ngOnInit() {
    super.ngOnInit();
    this.focusTextInputArea();
    this.store.selectOnce(state => state.personIdsState).subscribe(state => {
      // restore state
      this.setPersonIds(state.personIds.join('\n'));
    });
  }

  setPersonIds(personIds: string) {
    const result = personIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.personIds.personIds = personIds;
    this.store.dispatch(new SetPersonIds(result));
  }

  /**
  * Waits text input area element to load.
  * @returns promise
  */
   private async waitForTextInputAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.textArea !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 200);
    });
  }

  private focusTextInputArea() {
    this.waitForTextInputAreaToLoad().then(() => {
      this.textArea.nativeElement.focus();
    });
  }
}
