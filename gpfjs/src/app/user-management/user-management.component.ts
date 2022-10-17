import { Component, ElementRef, HostListener, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { UserGroup } from 'app/users-groups/users-groups';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { environment } from 'environments/environment';
import { Observable, ReplaySubject } from 'rxjs';
import { debounceTime, distinctUntilChanged, map, share, switchMap, take, tap } from 'rxjs/operators';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';

type TableName = 'USERS' | 'GROUPS' | 'DATASETS';

@Component({
  selector: 'gpf-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {
  public input$ = new ReplaySubject<string>(1);
  public users: User[] = [];
  public usersToShow$: Observable<User[]>;
  public groups: UserGroup[] | undefined;
  @ViewChild('searchBox') private searchBox: ElementRef;

  public imgPathPrefix = environment.imgPathPrefix;

  private pageCount = 0;
  private tableName: TableName = 'USERS';
  private loadingPage = true;

  public constructor(
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService,
    private router: Router,
    private route: ActivatedRoute
  ) { }

  public ngOnInit(): void {
    this.focusSearchBox();
    this.updateTable();

    this.route.queryParamMap.pipe(
      map(params => params.get('search') || ''),
      take(1)
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });
  }

  public search(value: string): void {
    this.input$.next(value);
  }

  private sortGroups(user: User): User {
    if (!user || !user.groups) {
      return user;
    }
    const defaultGroups = user.groups
      .filter(group => user.getDefaultGroups().indexOf(group) !== -1);
    let otherGroups = user.groups
      .filter(group => user.getDefaultGroups().indexOf(group) === -1);

    if (defaultGroups.length === 2 && defaultGroups[0] !== 'any_user') {
      const group = defaultGroups[0];
      defaultGroups[0] = defaultGroups[1];
      defaultGroups[1] = group;
    }

    otherGroups = otherGroups
      .sort((group1, group2) => group1.localeCompare(group2));

    user.groups = defaultGroups.concat(otherGroups);
    return user;
  }

  private async waitForSearchBoxToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchBox !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  public focusSearchBox(): void {
    this.waitForSearchBoxToLoad().then(() => {
      this.searchBox.nativeElement.focus();
    });
  }

  public onWindowScroll(): void {
    const pos = (document.documentElement.scrollTop || document.body.scrollTop) + document.documentElement.offsetHeight;
    const max = document.documentElement.scrollHeight;
    if (pos > max - 100) {
      this.updateTable();
    }
  }

  @HostListener('window:scroll', ['$event'])
  private updateTableOnScroll(): void {
    if (!this.loadingPage && window.scrollY + window.innerHeight + 200 > document.body.scrollHeight) {
      this.updateTable();
    }
  }

  public switchTableName(newName: TableName): void {
    this.tableName = newName;
    this.pageCount = 0;
    this.updateTable();
  }

  private updateTable(): void {
    this.pageCount++;
    this.loadingPage = true;

    switch (this.tableName) {
    case 'USERS':
      this.updateUsersTable();
      break;
    case 'GROUPS':
      this.updateGroupsTable();
      break;
    case 'DATASETS':
      // implement this.updateDatasetsTable()
      break;
    }
  }

  private updateUsersTable(): void {
    this.usersToShow$ = this.input$.pipe(
      map(searchTerm => searchTerm.trim()),
      debounceTime(300),
      distinctUntilChanged(),
      tap(searchTerm => {
        this.users = [];
        const queryParamsObject: any = {};
        if (searchTerm) {
          queryParamsObject.search = searchTerm;
        }
        this.router.navigate(['.'], {
          relativeTo: this.route,
          replaceUrl: true,
          queryParams: queryParamsObject
        });
      }),
      switchMap(searchTerm => this.usersService.searchUsersByGroup(searchTerm)),
      map(user => {
        this.users.push(this.sortGroups(user));
        return this.users;
      }),
      share()
    );

    // should be moved to user data subscribe
    this.loadingPage = false;
  }

  private updateGroupsTable(): void {
    this.usersGroupsService.getAllGroups().subscribe(res => {
      this.groups = this.groups.concat(res);
      this.loadingPage = false;
    });
  }
}
