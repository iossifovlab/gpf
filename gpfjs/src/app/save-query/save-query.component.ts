import { Observable } from 'rxjs';
import { Component, OnInit, Input, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { QueryService } from '../query/query.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { UsersService } from '../users/users.service';
import { Store } from '@ngxs/store';

@Component({
  selector: 'gpf-save-query',
  templateUrl: './save-query.component.html',
  styleUrls: ['./save-query.component.css']
})
export class SaveQueryComponent implements OnInit {

  @Input() queryType: string;
  @Input() disabled: boolean;
  @Input() stateSelector;

  @ViewChild('nameInput') nameInputRef: ElementRef;
  @ViewChild('descInput') descInputRef: ElementRef;
  @ViewChild(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu;
  userInfo$: Observable<any>;

  constructor(
    private store: Store,
    private queryService: QueryService,
    private usersService: UsersService,
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.userInfo$ = this.usersService.getUserInfoObservable().share();
  }

  saveUserQuery(name: string, description: string) {
    this.store.selectOnce(this.stateSelector).subscribe(state => {
     this.queryService.saveQuery(state, this.queryType)
       .take(1)
       .subscribe(response => {
         this.queryService.saveUserQuery(response['uuid'], name, description)
          .take(1)
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
