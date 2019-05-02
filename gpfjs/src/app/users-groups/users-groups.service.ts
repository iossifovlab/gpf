import { Injectable } from '@angular/core';
import { Http, RequestOptions } from '@angular/http';
import { UserGroup } from './users-groups';
import { Dataset } from '../datasets/datasets';

@Injectable()
export class UsersGroupsService {

  private groupsUrl = 'groups';
  private groupGrantPermissionUrl = 'groups/grant-permission';
  private groupRevokePermissionUrl = 'groups/revoke-permission';

  constructor(
    private http: Http,
  ) { }

  getAllGroups() {
    const options = new RequestOptions({ withCredentials: true });

    return this.http.get(this.groupsUrl, options)
      .map(response => UserGroup.fromJsonArray(response.json()));
  }

  getGroup(groupId: number) {
    const options = new RequestOptions({ withCredentials: true });

    return this.http.get(`${this.groupsUrl}/${groupId}`, options)
      .map(response => UserGroup.fromJson(response.json()));
  }

  grantPermission(groupName: string, dataset: Dataset) {
    const options = new RequestOptions({ withCredentials: true });

    return this.http.post(this.groupGrantPermissionUrl, {
      groupName: groupName,
      datasetId: dataset.id
    }, options);
  }

  revokePermission(group: UserGroup, dataset: Dataset) {
    const options = new RequestOptions({ withCredentials: true });

    return this.http.post(this.groupRevokePermissionUrl, {
      groupId: group.id,
      datasetId: dataset.id
    }, options);
  }

}
