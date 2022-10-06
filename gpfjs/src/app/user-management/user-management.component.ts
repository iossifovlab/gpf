import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { UserGroup } from 'app/users-groups/users-groups';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { environment } from 'environments/environment';
import { fromEvent, Observable, ReplaySubject, Subscription, zip } from 'rxjs';
import { debounceTime, distinctUntilChanged, map, share, switchMap, take, tap, throttleTime } from 'rxjs/operators';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';

type TableName = 'USERS' | 'GROUPS' | 'DATASETS';

@Component({
  selector: 'gpf-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit, OnDestroy {
  public input$ = new ReplaySubject<string>(1);
  public users: User[] = [];
  public usersToShow$: Observable<User[]>;
  public groups$: Observable<UserGroup[]>;
  @ViewChild('searchBox') private searchBox: ElementRef;

  public imgPathPrefix = environment.imgPathPrefix;

  private pageCount = 1;
  private tableName: TableName = 'USERS';
  private scrollEventSub: Subscription;

  public constructor(
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService,
    private router: Router,
    private route: ActivatedRoute
  ) { }

  public ngOnInit(): void {
    this.scrollEventSub = fromEvent(window, 'scroll').pipe(
      throttleTime(100), // ignore calls for certain time
      tap(() => this.onWindowScroll())
    ).subscribe();

    this.focusSearchBox();
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

    this.route.queryParamMap.pipe(
      map(params => params.get('search') || ''),
      take(1)
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });

    this.groups$ = this.usersGroupsService.getAllGroups();
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

  private updateTable(): void {
    this.pageCount++;

    if (this.tableName === 'GROUPS') {
      this.groups$ = zip(this.groups$, this.usersGroupsService.getAllGroups()).pipe(
        map(groups => groups[0].concat(groups[1]))
      );
    }
  }

  public switchTableName(newName: TableName): void {
    this.tableName = newName;
    // Reset pagecount
    this.pageCount = 1;
  }

  public ngOnDestroy(): void {
    this.scrollEventSub.unsubscribe();
  }
}
