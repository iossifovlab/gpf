import { Observable } from 'rxjs';
import { Component, OnInit, Input, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { QueryService } from '../query/query.service';
import { NgbDropdownMenu, NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { UsersService } from '../users/users.service';
import { Store } from '@ngxs/store';
import { DatasetsService } from 'app/datasets/datasets.service';
import { share, take } from 'rxjs/operators';
import { environment } from 'environments/environment';

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
  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  public userInfo$: Observable<any>;

  private urlUUID: string;
  public url: string;
  private savedUrlUUID: string;
  private copiedTimeoutHandle: NodeJS.Timeout;
  private savedTimeoutHandle: NodeJS.Timeout;
  public imgPathPrefix = environment.imgPathPrefix;
  public saveButtonText = 'Save';

  public constructor(
    private store: Store,
    private queryService: QueryService,
    private usersService: UsersService,
    private datasetsService: DatasetsService,
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  public ngOnInit(): void {
    this.userInfo$ = this.usersService.getUserInfoObservable().pipe(share());
  }

  public saveUserQuery(name: string, description: string): void {
    const datasetId = this.datasetsService.getSelectedDataset().id;

    this.store.selectOnce(state => state).subscribe(state => {
      state['datasetId'] = datasetId;
      this.queryService.saveQuery(state, this.queryType).pipe(take(1)).subscribe(response => {
        this.queryService.saveUserQuery(response['uuid'], name, description)
          .pipe(take(1))
          .subscribe(response => {
            if (response.hasOwnProperty('uuid')) {
              this.nameInputRef.nativeElement.value = '';
              this.descInputRef.nativeElement.value = '';
              this.saveButtonText = 'Saved';

              window.clearTimeout(this.savedTimeoutHandle);
              this.savedTimeoutHandle = setTimeout(() => {
                this.saveButtonText = 'Save';
              }, 2000);
            }
          });
      });
    });
  }

  public focusNameInput(): void {
    this.changeDetectorRef.detectChanges();
    this.nameInputRef.nativeElement.focus();
  }

  public openDropdown(opened: boolean): void {
    if (!opened) {
      this.resetUrl();
      return;
    }

    const datasetId = this.datasetsService.getSelectedDataset().id;
    this.store.selectOnce(state => state).subscribe(state => {
      state['datasetId'] = datasetId;

      this.queryService.saveQuery(state, this.queryType)
        .pipe(take(1))
        .subscribe(response => {
          this.urlUUID = response['uuid'];
          this.setUrl();
        });
    },
    error => {
      this.resetUrl();
    }
    );
  }

  private resetUrl(): void {
    this.savedUrlUUID = null;
    this.url = null;
  }

  private setUrl(): void {
    if (!this.urlUUID) {
      return;
    }

    if (this.savedUrlUUID !== this.urlUUID) {
      this.url = this.queryService.getLoadUrl(this.urlUUID);
      this.savedUrlUUID = this.urlUUID;
    }
  }

  public openCopiedTooltip(): void {
    this.copiedTooltip.open();
    window.clearTimeout(this.copiedTimeoutHandle);
    this.copiedTimeoutHandle = setTimeout(() => {
      this.copiedTooltip.close();
    }, 2000);
  }
}
