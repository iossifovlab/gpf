import { Injectable } from '@angular/core';
import { CanActivate, CanActivateChild, CanLoad, Route,
         UrlSegment, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';

import { DatasetsService } from './datasets/datasets.service';

type CanActivateReturnType = Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree;

@Injectable({ providedIn: 'root' })
export class DatasetPermissionGuard implements CanActivateChild {
  selds;
  constructor(private datasetsService: DatasetsService) {
    this.datasetsService.getSelectedDatasetObservable().subscribe(res => {
      this.selds = res;
    });
  }

  public canActivateChild(next: ActivatedRouteSnapshot, state: RouterStateSnapshot): CanActivateReturnType {
    console.log('can activate child');
    return this.selds ? this.selds.accessRights : true;
  }
}
