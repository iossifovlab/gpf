import { Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { UserGroup } from 'app/users-groups/users-groups';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { environment } from 'environments/environment';
import { map, take } from 'rxjs/operators';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';

type TableName = 'USERS' | 'GROUPS' | 'DATASETS';

@Component({
  selector: 'gpf-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {
  public users: User[] = [];
  public groups: UserGroup[] = [];
  public searchText = '';
  @ViewChild('searchBox') private searchBox: ElementRef;
  public currentUserEmail: string;
  public imgPathPrefix = environment.imgPathPrefix;

  private pageCount = 0;
  private tableName: TableName = 'USERS';
  private loadingPage = true;
  private allPagesLoaded = false;

  public constructor(
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService,
    private route: ActivatedRoute
  ) { }

  public ngOnInit(): void {
    this.focusSearchBox();
    this.updateCurrentTable();

    this.route.queryParamMap.pipe(
      map(params => params.get('search') || ''),
      take(1)
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });

    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser: User) => {
      this.currentUserEmail = currentUser.email;
    });
  }

  public search(value: string): void {
    this.searchText = value;
    this.resetTablesData();
    this.updateCurrentTable();
  }

  public resetTablesData(): void {
    this.pageCount = 0;
    this.users = [];
    this.groups = [];
    // this.datasets = [];
    this.allPagesLoaded = false;
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

  // Needed?
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

  @HostListener('window:scroll', ['$event'])
  public updateTableOnScroll(): void {
    if (!this.loadingPage && window.scrollY + window.innerHeight + 200 > document.body.scrollHeight) {
      this.updateCurrentTable();
    }
  }

  public switchTableName(newName: TableName): void {
    this.tableName = newName;
    this.searchText = '';
    this.resetTablesData();
    this.updateCurrentTable();
  }

  public updateCurrentTable(): void {
    if (!this.allPagesLoaded) {
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
  }

  private updateUsersTable(): void {
    this.usersService.getUsers(this.pageCount, this.searchText).subscribe(res => {
      if (!res.length) {
        this.allPagesLoaded = true;
        return;
      }
      res = res.map(user => this.sortGroups(user));
      this.users = this.users.concat(res);
      this.loadingPage = false;
    });
  }

  private updateGroupsTable(): void {
    this.usersGroupsService.getGroups(this.pageCount, this.searchText).subscribe(res => {
      if (!res.length) {
        this.allPagesLoaded = true;
        return;
      }
      this.groups = this.groups.concat(res);
      this.loadingPage = false;
    });
  }
}
