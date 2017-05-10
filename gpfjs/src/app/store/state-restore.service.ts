import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';
import { ReplaySubject } from 'rxjs/ReplaySubject';
import { Router } from '@angular/router';

import 'rxjs/add/operator/map';

@Injectable()
export class StateRestoreService {
  private state = new ReplaySubject<any>(1);
  private firstUrl: string;
  private emptyObjectSend = false;
  private subscribedKeys = new Set<String>();

  constructor(
    private router: Router
  ) {
    //Reset state when tool/dataset is changed
    //This prevents restoring the initial state constantly
    router.events.subscribe(
      (params) => {
        let newUrl = this.router.url.split(';')[0];
        if (this.firstUrl == null) {
          this.firstUrl = newUrl;
        } else if (!this.emptyObjectSend && this.firstUrl !== newUrl) {
          this.state.next({});
          this.emptyObjectSend = true;
        }
      }
    );
  }

  getState(key: string): Observable<any> {
    if (this.subscribedKeys.has(key)) {
      return Observable.of({});
    } else {
      this.subscribedKeys.add(key);
      return this.state;
    }
  }

  onParamsUpdate(jsonEncodedState: string) {
    if (jsonEncodedState && jsonEncodedState.length > 0) {
      let currentState = JSON.parse(jsonEncodedState);
      this.state.next(currentState);
    }
  }


}
