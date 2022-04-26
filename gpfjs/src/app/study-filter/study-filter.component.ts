import { Component, Input, Output, EventEmitter } from '@angular/core';
import { IsNotEmpty } from 'class-validator';
import { environment } from 'environments/environment';

export class Study {
  @IsNotEmpty() public studyId: string;
  @IsNotEmpty() public studyName: string;

  public constructor(studyId: string, studyName: string) {
    this.studyId = studyId;
    this.studyName = studyName;
  }
}

@Component({
  selector: 'gpf-study-filter',
  templateUrl: './study-filter.component.html',
  styleUrls: ['./study-filter.component.css']
})
export class StudyFilterComponent {
  @Input() public studies: Study[];
  @Input() public selectedStudy: Study;
  @Input() public errors: string[];
  @Output() public changeSelectedStudyEvent = new EventEmitter<object>();

  public imgPathPrefix = environment.imgPathPrefix;

  public set selectedStudyNames(selectedStudyId: string) {
    this.changeSelectedStudyEvent.emit({
      selectedStudy: this.selectedStudy,
      selectedStudyId: selectedStudyId
    });
  }

  public get selectedStudyNames(): string {
    return this.selectedStudy.studyId;
  }
}
