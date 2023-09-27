import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonReportsRowComponent } from './common-reports-row.component';
import { SearchableSelectComponent } from 'app/searchable-select/searchable-select.component';

describe('CommonReportsRowComponent', () => {
  let component: CommonReportsRowComponent;
  let fixture: ComponentFixture<CommonReportsRowComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CommonReportsRowComponent, SearchableSelectComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(CommonReportsRowComponent);
    component = fixture.componentInstance;
    component.pedigreeGroup = [{
      counterId: 1,
      groupName: 'groupName',
      data: [{
        pedigreeIdentifier: 'pi',
        id: 'id',
        father: 'dad',
        mother: 'mom',
        gender: 'M',
        role: 'prb',
        color: 'F0F0F0',
        position: [5, 10],
        generated: true,
        label: 'label',
        smallLabel: 'sl'
      }],
      count: 1, tags: ['tag1', 'tag2']
    }];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
