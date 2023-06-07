import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FamilyIds } from './family-ids';
import { ValidateNested } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetFamilyIds, FamilyIdsState} from './family-ids.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css'],
})
export class FamilyIdsComponent extends StatefulComponent implements OnInit {
  @ValidateNested()
  public familyIds = new FamilyIds();
  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store) {
    super(store, FamilyIdsState, 'familyIds');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.focusTextInputArea();
    this.store.selectOnce(state => state.familyIdsState).subscribe(state => {
      // restore state
      this.setFamilyIds(state.familyIds.join('\n'));
    });
  }

  public setFamilyIds(familyIds: string): void {
    const result = familyIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.familyIds.familyIds = familyIds;
    this.store.dispatch(new SetFamilyIds(result));
  }

  /**
   * Waits text input area element to load.
   *
   * @returns promise
   */
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
}
