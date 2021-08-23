import { Injectable } from '@angular/core';
import { CanActivate, CanActivateChild, CanLoad, Route, UrlSegment, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';

import { DatasetsService } from './datasets/datasets.service';
import { Dataset } from './datasets/datasets';

@Injectable({
  providedIn: 'root'
})
export class DatasetPermissionGuard implements CanActivate, CanActivateChild, CanLoad {
  selectedDataset: Dataset;
  hasPermission = false;

  constructor(
    private datasetsService: DatasetsService,
  ) { }

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return true;
  }
  canActivateChild(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return true;
  }
  canLoad(
    route: Route,
    segments: UrlSegment[]): Observable<boolean> | Promise<boolean> | boolean {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    this.datasetsService.getDatasetsLoadedObservable()
    .subscribe(datasetsLoaded => {
      this.selectedDataset = this.datasetsService.getSelectedDataset();
      if (!this.selectedDataset) { return; }
      this.hasPermission = this.selectedDataset.accessRights;
    });
    return this.hasPermission;
  }
}
