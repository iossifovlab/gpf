
import {throwError as observableThrowError,  ReplaySubject, Observable, Subscription} from 'rxjs';
import {Scheduler} from 'rxjs-compat';
import { DoCheck, OnDestroy, QueryList, ViewChildren, forwardRef } from '@angular/core';

import { validationErrorsToStringArray, toValidationObservable } from '../utils/to-observable-with-validation';
import { SaveQuery } from '../query/common-query-data';


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
        return observableThrowError(
          `${this.constructor.name}: invalid state`,
          Scheduler.async);
      });
  }

}

export abstract class QueryStateCollector implements DoCheck, OnDestroy, SaveQuery {
  private stateObjectString = '';
  private stateChange$ = new ReplaySubject<boolean>(1);
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
    for (const subscruption of this.subscriptions) {
      subscruption.unsubscribe();
    }
    this.subscriptions = new Array<Subscription>();
  }

  getCurrentState() {
      const state = this.collectState();

      return Observable.zip(...state, function(...states) {
        const stateJSON = {};
        for (const st of  states) {
          for (const key in st) {
            if (key in stateJSON) {
              stateJSON[key] = {...stateJSON[key], ...st[key]};
            } else {
              stateJSON[key] = st[key];
            }
          }
        }
        return stateJSON;
      })
        .map(state => {
          const stateObject = Object.assign({}, ...state);
          return stateObject;
        });
    }

  getStateChange() {
    this.stateObjectString = '';

    const observable = Observable
      .merge(this.stateChange$, this.directContentChildren.changes, this.contentChildren.changes)
      .subscribeOn(Scheduler.queue)
      .share();

    return Observable.concat(observable.first(), observable.skip(1).debounceTime(200))
      .switchMap(_ => {
        const stateArray = this.collectState();
        return Observable.zip(...stateArray, function(...states) {
          const stateJSON = {};
          for (const st of  states) {
            for (const key in st) {
              if (key in stateJSON) {
                stateJSON[key] = {...stateJSON[key], ...st[key]};
              } else {
                stateJSON[key] = st[key];
              }
            }
          }
          return stateJSON;
        })
          .catch(error => {
            return Observable.of([]);
          })
          .map(state => {
            if (!state || state.length === 0) {
              return '';
            }

            const stateString = JSON.stringify(Object.assign({}, ...state));
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
