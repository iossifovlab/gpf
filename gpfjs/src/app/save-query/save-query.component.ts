import { Observable } from 'rxjs';
import { Component, OnInit, Input, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { QueryService } from '../query/query.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { UsersService } from '../users/users.service';
import { Store } from '@ngxs/store';
import { DatasetsService } from 'app/datasets/datasets.service';
import { share, take } from 'rxjs/operators';

@Component({
  selector: 'gpf-save-query',
  templateUrl: './save-query.component.html',
  styleUrls: ['./save-query.component.css']
})
export class SaveQueryComponent implements OnInit {
  @Input() public queryType: string;
  @Input() public disabled: boolean;

  @ViewChild('nameInput') public nameInputRef: ElementRef;
  @ViewChild('descInput') public descInputRef: ElementRef;
  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  public userInfo$: Observable<any>;

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
            }
          });
      });
    });

   this.ngbDropdownMenu.dropdown.close();
  }

  public focusNameInput(): void {
    this.changeDetectorRef.detectChanges();
    this.nameInputRef.nativeElement.focus();
  }
}
