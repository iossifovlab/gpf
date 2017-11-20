import { AfterContentInit, ContentChildren, QueryList, ViewChildren, forwardRef, DoCheck } from '@angular/core';

import { Subject, Observable } from 'rxjs';
import { Scheduler } from 'rxjs';

import { GeneSetsComponent } from '../gene-sets/gene-sets.component';
import { GenesBlockComponent } from '../genes-block/genes-block.component';
import { UsersComponent } from '../users/users.component';
import { GenderComponent } from '../gender/gender.component';

import * as _ from 'lodash';


export class QueryStateProvider implements DoCheck {
  stateChange$ = new Subject<boolean>();
  private lastState: any;

  getState() {
    return null;
  }

  ngDoCheck() {
    this.stateChange$.next(true);
  }
}


export class QueryStateCollector {
  @ViewChildren(forwardRef(() => QueryStateProvider))
  directContentChildren: QueryList<QueryStateProvider>;

  @ViewChildren(forwardRef(() => QueryStateCollector))
  contentChildren: QueryList<QueryStateCollector>;

  collectState() {
    let directState = this.directContentChildren.map((children) => children.getState());
    let indirectState = this.contentChildren.reduce((acc, current) => acc.concat(current.collectState()), []);
    return directState.concat(indirectState);
  }

  getDirectStateChange() {
    return this.directContentChildren.map(children => children.stateChange$);
  }

  getStateObservables(): Subject<boolean>[] {
    let directState = this.getDirectStateChange();
    let indirectState = this.contentChildren
      .reduce((acc, current) => acc.concat(current.getStateObservables()), new Array<Subject<boolean>>());
    return _.flattenDeep(directState.concat(indirectState));
  }

  getStateChange() {
    let so = this.getStateObservables();

    return Observable.merge(...so)
      .subscribeOn(Scheduler.async)
      .debounceTime(500);
  }

  detectNextStateChange(lambda: () => any) {
    this.getStateChange()
      .take(1)
      .subscribe(_ => {
        console.log("change run");
        lambda();
        this.detectNextStateChange(lambda);
      });
  }
}
