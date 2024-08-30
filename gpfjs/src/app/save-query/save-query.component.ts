import { Observable } from 'rxjs';
import { Component, OnInit, Input, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { QueryService } from '../query/query.service';
import { NgbDropdown, NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { UsersService } from '../users/users.service';
import { Store} from '@ngrx/store';
import { share, switchMap, take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { UserInfo } from 'app/users/users';

@Component({
  selector: 'gpf-save-query',
  templateUrl: './save-query.component.html',
  styleUrls: ['./save-query.component.css'],
})
export class SaveQueryComponent implements OnInit {
  @Input() public queryType: string;
  @Input() public disabled: boolean;

  @ViewChild('nameInput') public nameInputRef: ElementRef;
  @ViewChild('descInput') public descInputRef: ElementRef;
  @ViewChild('copiedTooltip') public copiedTooltip: NgbTooltip;
  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;

  public userInfo$: Observable<UserInfo>;

  private urlUUID: string;
  public url: string;
  private copiedTimeoutHandle: NodeJS.Timeout;
  private savedTimeoutHandle: NodeJS.Timeout;
  public imgPathPrefix = environment.imgPathPrefix;
  public saveButtonText = 'Save';

  public constructor(
    private store: Store,
    private queryService: QueryService,
    private usersService: UsersService,
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  public ngOnInit(): void {
    this.userInfo$ = this.usersService.getUserInfoObservable().pipe(share());
  }

  public saveUserQuery(name: string, description: string): void {
    this.nameInputRef.nativeElement.value = '';
    this.descInputRef.nativeElement.value = '';

    this.store.pipe(
      switchMap(state => this.queryService.saveQuery(state, this.queryType).pipe(take(1))),
      switchMap((response: {uuid: string}) =>
        this.queryService.saveUserQuery(response.uuid, name, description).pipe(take(1)))
    ).subscribe((response: {uuid: string}) => {
      if (response.uuid) {
        this.saveButtonText = 'Saved';
        window.clearTimeout(this.savedTimeoutHandle);
        this.savedTimeoutHandle = setTimeout(() => {
          this.saveButtonText = 'Save';
        }, 2000);
      }
    });
  }

  public focusNameInput(): void {
    this.changeDetectorRef.detectChanges();
    this.nameInputRef.nativeElement.focus();
  }

  public toggleDropdown(): void {
    if (this.dropdown.isOpen()) {
      this.dropdown.close();
      this.resetUrl();
      return;
    }

    this.store.pipe(
      switchMap(state => this.queryService.saveQuery(state, this.queryType).pipe(take(1)))
    ).subscribe({
      next: (response: {uuid: string}) => {
        this.urlUUID = response.uuid;
        this.setUrl();
        this.dropdown.open();
      },
      error: () => this.resetUrl()
    });
  }

  private resetUrl(): void {
    this.url = null;
  }

  private setUrl(): void {
    if (!this.urlUUID) {
      return;
    }

    this.url = this.queryService.getLoadUrl(this.urlUUID);
  }

  public openCopiedTooltip(): void {
    this.copiedTooltip.open();
    window.clearTimeout(this.copiedTimeoutHandle);
    this.copiedTimeoutHandle = setTimeout(() => {
      this.copiedTooltip.close();
    }, 2000);
  }
}
