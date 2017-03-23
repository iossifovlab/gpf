import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';
import { ReplaySubject } from 'rxjs/ReplaySubject';

import 'rxjs/add/operator/map';

@Injectable()
export class StateRestoreService {
  public state = new ReplaySubject<any>(1);


  constructor(
  ) {
  }

  onParamsUpdate(jsonEncodedState: string) {
    if (jsonEncodedState && jsonEncodedState.length > 0) {
      let currentState = JSON.parse(jsonEncodedState);
      this.state.next(currentState);
    }
  }


}
