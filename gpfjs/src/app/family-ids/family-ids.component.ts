import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FamilyIds } from './family-ids';
import { ValidateNested } from 'class-validator';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { Store } from '@ngrx/store';
import { selectFamilyIds, setFamilyIds } from './family-ids.state';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html'
})
export class FamilyIdsComponent extends StatefulComponentNgRx implements OnInit {
  @ValidateNested()
  public familyIds = new FamilyIds();
  @ViewChild('textArea') private textArea: ElementRef;

  public constructor(protected store: Store) {
    super(store, 'familyIds', selectFamilyIds);
  }

  public ngOnInit(): void {
    super.ngOnInit();

    this.focusTextInputArea();
    this.store.select(selectFamilyIds).pipe(take(1)).subscribe((familyIds: string[]) => {
      // restore state
      this.setFamilyIds(familyIds.join('\n')); // must join on more conditions most likely
    });
  }

  public setFamilyIds(familyIds: string): void {
    const result = familyIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.familyIds.familyIds = familyIds;
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
}
