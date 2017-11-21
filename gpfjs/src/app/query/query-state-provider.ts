import { DoCheck, ContentChildren, QueryList, ViewChildren, forwardRef, OnChanges } from '@angular/core';

import { Subject, Observable } from 'rxjs';
import { Scheduler } from 'rxjs';

import { GeneSetsComponent } from '../gene-sets/gene-sets.component';
import { GenesBlockComponent } from '../genes-block/genes-block.component';
import { UsersComponent } from '../users/users.component';
import { GenderComponent } from '../gender/gender.component';

import * as _ from 'lodash';


export class QueryStateProvider {
  getState() {
    return null;
  }
}


export class QueryStateCollector implements DoCheck {
  private stateObjectString = '';
  private stateChange$ = new Subject<boolean>();

  @ViewChildren(forwardRef(() => QueryStateProvider))
  directContentChildren: QueryList<QueryStateProvider>;

  @ViewChildren(forwardRef(() => QueryStateCollector))
  contentChildren: QueryList<QueryStateCollector>;

  collectState() {
    let directState = [];
    let indirectState = [];
    if (this.directContentChildren) {
      directState = this.directContentChildren.map((children) => children.getState());
    }
    if (this.contentChildren) {
      indirectState = this.contentChildren.reduce((acc, current) => acc.concat(current.collectState()), []);
    }
    return directState.concat(indirectState);
  }

  ngDoCheck() {
    this.stateChange$.next(true);
  }

  getStateChange() {
    let observable = Observable
      .combineLatest(this.stateChange$, this.directContentChildren.changes, this.contentChildren.changes)
      .subscribeOn(Scheduler.async)
      .share();

    return Observable.concat(observable.first(), observable.skip(1).debounceTime(500))
      .switchMap(_ => {
        let stateArray = this.collectState();
        return Observable.zip(...stateArray)
          .catch(error => {
            return Observable.of([]);
          })
          .map(state => {
            if (!state || state.length === 0) {
              return this.stateObjectString;
            }
            let stateString = JSON.stringify(Object.assign({}, ...state));
            if (stateString !== this.stateObjectString) {
              this.stateObjectString = stateString;
            }
            return this.stateObjectString;
          });
      })
      .distinctUntilChanged();
  }

  detectNextStateChange(lambda: () => any) {
    this.getStateChange()
      .subscribe(_ => {
        console.log("change detected");
        lambda();
      });
  }
}
