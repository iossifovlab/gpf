import { Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { DatasetPermissions } from 'app/datasets-table/datasets-table';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UserGroup } from 'app/users-groups/users-groups';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { environment } from 'environments/environment';
import { Observable, Subscription, of } from 'rxjs';
import { catchError, take } from 'rxjs/operators';
import { User, UserInfo } from '../users/users';
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
  public datasets: DatasetPermissions[] = [];
  public searchText = '';
  public currentUserEmail: string;
  public imgPathPrefix = environment.imgPathPrefix;
  public createMode = false;

  public creationError = '';
  @ViewChild('searchBox') private searchBox: ElementRef;
  @ViewChild('nameBox') private nameBox: ElementRef;
  @ViewChild('emailBox') private emailBox: ElementRef;
  @ViewChild('groupNameBox') private groupNameBox: ElementRef;
  private getPageSubscription: Subscription = new Subscription();
  private pageCount = 0;
  private tableName: TableName = 'USERS';
  private allPagesLoaded = false;

  public constructor(
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService,
    private datasetsService: DatasetsService
  ) { }

  public ngOnInit(): void {
    this.focusSearchBox();
    this.updateCurrentTable();

    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser: UserInfo) => {
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
    this.datasets = [];
    this.allPagesLoaded = false;
  }

  private async waitForSearchBoxToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchBox !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  public focusSearchBox(): void {
    this.waitForSearchBoxToLoad().then(() => {
      (this.searchBox.nativeElement as HTMLInputElement).focus();
    });
  }

  public createUser(name: string, email: string): void {
    if (!this.isNameValid(name)) {
      (this.nameBox.nativeElement as HTMLInputElement).focus();
      return;
    }
    if (!this.isEmailValid(email)) {
      (this.emailBox.nativeElement as HTMLInputElement).focus();
      return;
    }
    const newUser = new User(null, name, email, ['any_user', email], false, []);

    this.usersService.createUser(newUser)
      .pipe(catchError((err: {error: { email: string[] } }) => {
        this.creationError = `Error: ${err.error.email[0]}`;
        return of(null);
      }))
      .subscribe((user: User) => {
        if (user !== null) {
          this.cancelCreation();
          this.users.unshift(user);
        }
      });
  }

  public createGroup(name: string): void {
    if (!this.isNameValid(name)) {
      (this.groupNameBox.nativeElement as HTMLInputElement).focus();
      return;
    }

    this.usersGroupsService.getGroup(name)
      // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
      .pipe(catchError(_ => {
        this.cancelCreation();
        const newGroup = new UserGroup(null, name, [], []);
        this.groups.unshift(newGroup);
        return of(null);
      }))
      .subscribe((group: UserGroup) => {
        if (group !== null) {
          this.creationError = `'${group.name}' already exists choose another name!`;
        }
      });
  }

  public cancelCreation(): void {
    this.creationError = '';
    this.createMode = false;
  }

  private isEmailValid(email: string): boolean {
    const re = new RegExp(/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/);
    return re.test(String(email).toLowerCase());
  }

  private isNameValid(name: string): boolean {
    const re = new RegExp(/.{3,}/);
    return re.test(String(name).toLowerCase());
  }

  @HostListener('window:scroll', ['$event'])
  public updateTableOnScroll(): void {
    if (this.getPageSubscription.closed && window.scrollY + window.innerHeight + 200 > document.body.scrollHeight) {
      this.updateCurrentTable();
    }
  }

  public switchTableName(newName: TableName): void {
    this.tableName = newName;
    this.createMode = false;
    this.searchText = '';
    this.creationError = '';
    this.resetTablesData();
    this.updateCurrentTable();
  }

  public updateCurrentTable(): void {
    if (!this.allPagesLoaded) {
      this.pageCount++;

      switch (this.tableName) {
        case 'USERS':
          this.updateTable(this.usersService.getUsers.bind(this.usersService));
          break;
        case 'GROUPS':
          this.updateTable(this.usersGroupsService.getGroups.bind(this.usersGroupsService));
          break;
        case 'DATASETS':
          this.updateTable(this.datasetsService.getManagementDatasets.bind(this.datasetsService));
          break;
      }
    }
  }

  private updateTable(
    getPage: (page: number, searchString: string) => Observable<User[] | UserGroup[] | DatasetPermissions[]>
  ): void {
    this.getPageSubscription?.unsubscribe();
    this.getPageSubscription = getPage(this.pageCount, this.searchText).subscribe(res => {
      if (!res.length) {
        this.allPagesLoaded = true;
        return;
      }

      res.forEach(r => {
        if (r instanceof User) {
          this.users.push(r);
        } else if (r instanceof UserGroup) {
          this.groups.push(r);
        } else if (r instanceof DatasetPermissions) {
          this.datasets.push(r);
        }
      });

      this.getPageSubscription.unsubscribe();
    });
  }
}
