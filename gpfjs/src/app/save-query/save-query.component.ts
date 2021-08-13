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

  @Input() queryType: string;
  @Input() disabled: boolean;

  @ViewChild('nameInput') nameInputRef: ElementRef;
  @ViewChild('descInput') descInputRef: ElementRef;
  @ViewChild(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu;
  userInfo$: Observable<any>;

  constructor(
    private store: Store,
    private queryService: QueryService,
    private usersService: UsersService,
    private datasetsService: DatasetsService,
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.userInfo$ = this.usersService.getUserInfoObservable().pipe(share());
  }

  saveUserQuery(name: string, description: string) {
    const datasetId = this.datasetsService.getSelectedDatasetId();
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

  focusNameInput() {
    this.changeDetectorRef.detectChanges();
    this.nameInputRef.nativeElement.focus();
  }
}
