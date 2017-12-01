import { DoCheck, OnDestroy, ContentChildren, QueryList, ViewChildren, forwardRef, OnChanges } from '@angular/core';

import { BehaviorSubject, Observable, Subscription } from 'rxjs';
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

export abstract class QueryStateCollector implements DoCheck, OnDestroy {
  private stateObjectString = '';
  private stateChange$ = new BehaviorSubject<boolean>(true);
  private subscriptions = new Array<Subscription>();

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

  ngOnDestroy() {
    for (let subscruption of this.subscriptions) {
      subscruption.unsubscribe();
    }
    this.subscriptions = new Array<Subscription>();
  }

  getStateChange() {
    this.stateObjectString = '';

    let observable = Observable
      .merge(this.stateChange$, this.directContentChildren.changes, this.contentChildren.changes)
      .subscribeOn(Scheduler.queue)
      .share();

    return Observable.concat(observable.first(), observable.skip(1).debounceTime(200))
      .switchMap(_ => {
        let stateArray = this.collectState();
        return Observable.zip(...stateArray)
          .catch(error => {
            return Observable.of([]);
          })
          .map(state => {
            if (!state || state.length === 0) {
              return '';
            }

            let stateString = JSON.stringify(Object.assign({}, ...state));
            if (stateString !== this.stateObjectString) {
              this.stateObjectString = stateString;
            }
            return this.stateObjectString;
          });
      })
      .distinctUntilChanged()
      .subscribeOn(Scheduler.queue);
  }

  detectNextStateChange(lambda: () => any) {
    this.subscriptions.push(this.getStateChange()
      .subscribe(_ => {
        lambda();
      }));
  }
}
