import { DoCheck, ContentChildren, QueryList, ViewChildren, forwardRef, OnChanges } from '@angular/core';

import { Subject, Observable } from 'rxjs';
import { Scheduler } from 'rxjs';

import { validationErrorsToStringArray, toValidationObservable } from '../utils/to-observable-with-validation';

import * as _ from 'lodash';


export abstract class QueryStateProvider {
  abstract getState(): Observable<object>;
}

export abstract class QueryStateWithErrorsProvider extends QueryStateProvider {

  errors: string[] | string[][];

  protected validateAndGetState(object): Observable<any> {
    return toValidationObservable(object)
      .map(value => {
        this.errors = [];
        return value;
      })
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        return Observable.throw(
          `${this.constructor.name}: invalid state`,
          Scheduler.async);
      });
  }

}

export abstract class QueryStateCollector implements DoCheck {
  private stateObjectString = '';
  private stateChange$ = new Subject<boolean>();

  @ViewChildren(forwardRef(() => QueryStateProvider))
  directContentChildren: QueryList<QueryStateProvider>;

  @ViewChildren(forwardRef(() => QueryStateCollector))
  contentChildren: QueryList<QueryStateCollector>;

  collectState() {
    let directState = [];
    let indirectState = [];
    if (this.directContentChildren && this.directContentChildren.length > 0) {
      directState = this.directContentChildren
        .map(children => children.getState());
    }
    if (this.contentChildren && this.contentChildren.length > 0) {
      indirectState = this.contentChildren
        .reduce((acc, current) => acc.concat(current.collectState()), []);
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
            console.warn(error);
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
