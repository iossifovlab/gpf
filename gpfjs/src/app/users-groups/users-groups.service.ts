import { Injectable } from '@angular/core';
import { Http, RequestOptions } from '@angular/http';
import { UserGroup } from './users-groups';

@Injectable()
export class UsersGroupsService {

  private groupsUrl = 'groups';

  constructor(
    private http: Http,
  ) { }

  getAllGroups() {
    let options = new RequestOptions({ withCredentials: true });

    return this.http.get(this.groupsUrl, options)
      .map(response => response.json()['results'] as UserGroup[]);
  }

}
