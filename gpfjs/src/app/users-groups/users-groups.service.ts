import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { UserGroup } from './users-groups';
import { Dataset } from '../datasets/datasets';
import { ConfigService } from '../config/config.service';

@Injectable()
export class UsersGroupsService {
  private readonly groupsUrl = 'groups';
  private readonly groupGrantPermissionUrl = 'groups/grant-permission';
  private readonly groupRevokePermissionUrl = 'groups/revoke-permission';

  constructor(
    private http: HttpClient,
    private config: ConfigService,
  ) {}

  getAllGroups() {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.groupsUrl, options)
      .map((response: any) => UserGroup.fromJsonArray(response));
  }

  getGroup(groupId: number) {
    const options = { withCredentials: true };

    return this.http.get(`${this.config.baseUrl}${this.groupsUrl}/${groupId}`, options)
      .map((response: any) => UserGroup.fromJson(response));
  }

  grantPermission(groupName: string, dataset: Dataset) {
    const options = { withCredentials: true };

    return this.http.post(this.config.baseUrl + this.groupGrantPermissionUrl, {
      groupName: groupName,
      datasetId: dataset.id
    }, options);
  }

  revokePermission(group: UserGroup, dataset: Dataset) {
    const options = { withCredentials: true };

    return this.http.post(this.config.baseUrl + this.groupRevokePermissionUrl, {
      groupId: group.id,
      datasetId: dataset.id
    }, options);
  }
}
