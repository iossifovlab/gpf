import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Observable, of } from 'rxjs';
import { StudyFiltersBlockComponent } from './study-filters-block.component';
import { By } from '@angular/platform-browser';
import { NgbNavModule, NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { SimpleChange } from '@angular/core';
import { StudyFilterComponent } from 'app/study-filter/study-filter.component';
import { RemoveButtonComponent } from 'app/remove-button/remove-button.component';
import { AddButtonComponent } from 'app/add-button/add-button.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FormsModule } from '@angular/forms';
import { NgxsModule } from '@ngxs/store';

const datasetConfigMock: any = {
  studies: ['test_id1', 'test_id2'],
  studyNames: ['test_name1', 'test_name2']
};

describe('StudyFiltersBlockComponent', () => {
  let component: StudyFiltersBlockComponent;
  let fixture: ComponentFixture<StudyFiltersBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        StudyFiltersBlockComponent,
        StudyFilterComponent,
        RemoveButtonComponent,
        AddButtonComponent,
        ErrorsAlertComponent
      ],
      providers: [NgbNavModule, NgbModule, FormsModule],
      imports: [NgbNavModule, NgbModule, FormsModule, NgxsModule.forRoot([])],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyFiltersBlockComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce(f) {
        return of({studyFilters: ['value1', 'value2']});
      },
      dispatch(set) {}
    } as any;
    fixture.detectChanges();
    component.dataset = datasetConfigMock;
    component.ngOnChanges({'dataset': new SimpleChange(null, datasetConfigMock, true)});
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should correctly display names and not ids', () => {
    component.addFilter();
    fixture.detectChanges();
    const options = fixture.debugElement.queryAll(By.css('option'));
    for (let i = 0; i < options.length; i++) {
      expect(component.dataset.studyNames.indexOf(options[i].nativeElement.textContent.trim())).not.toBe(-1);
    }
  });
});
