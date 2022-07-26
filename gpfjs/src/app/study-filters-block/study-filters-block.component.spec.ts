import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { of } from 'rxjs';
import { StudyFiltersBlockComponent } from './study-filters-block.component';
import { NgbNavModule, NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { RemoveButtonComponent } from 'app/remove-button/remove-button.component';
import { AddButtonComponent } from 'app/add-button/add-button.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FormsModule } from '@angular/forms';
import { NgxsModule } from '@ngxs/store';

const datasetConfigMock: any = {
  studyNames: ['test_name1', 'test_name2']
};

describe('StudyFiltersBlockComponent', () => {
  let component: StudyFiltersBlockComponent;
  let fixture: ComponentFixture<StudyFiltersBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        StudyFiltersBlockComponent,
        RemoveButtonComponent,
        AddButtonComponent,
        ErrorsAlertComponent
      ],
      providers: [NgbNavModule, NgbModule, FormsModule],
      imports: [NgbNavModule, NgbModule, FormsModule, NgxsModule.forRoot([], {developmentMode: true})],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyFiltersBlockComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce() {
        return of({studyFilters: ['value1', 'value2']});
      },
      dispatch() {}
    } as any;
    component.dataset = datasetConfigMock;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
