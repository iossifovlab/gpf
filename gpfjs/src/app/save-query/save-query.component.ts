import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider';
import { QueryService } from '../query/query.service';

@Component({
  selector: 'gpf-save-query',
  templateUrl: './save-query.component.html',
  styleUrls: ['./save-query.component.css']
})
export class SaveQueryComponent implements OnInit {

  @Input() queryType: string;
  @ViewChild('nameInput') nameInputRef: ElementRef
  @ViewChild('descInput') descInputRef: ElementRef
  queryWasSaved: boolean = false;

  constructor(
    private queryService: QueryService,
    private parentComponent: QueryStateCollector
  ) { };

  ngOnInit() {}

  saveUserQuery(name: string, description: string) {
     this.parentComponent.getCurrentState()
       .take(1)
       .subscribe(state => {
           this.queryService.saveQuery(state, this.queryType)
               .take(1)
               .subscribe(response => {
                   this.queryService.saveUserQuery(response['uuid'], name, description)
                    .take(1)
                    .subscribe(response => {
                      if(response.status == 201) {
                        this.queryWasSaved = true;
                        this.nameInputRef.nativeElement.value = '';
                        this.descInputRef.nativeElement.value = '';
                        setTimeout(() => { this.queryWasSaved = false }, 2000);
                      }
                    });
               });
       },
       error => {});
  }
}
