import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { StateRestoreService } from 'app/store/state-restore.service';
import { CategoricalFilterComponent } from './categorical-filter.component';

describe('CategoricalFilterComponent', () => {
  let component: CategoricalFilterComponent;
  let fixture: ComponentFixture<CategoricalFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [CategoricalFilterComponent],
      providers: [StateRestoreService],
      imports: [FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CategoricalFilterComponent);
    component = fixture.componentInstance;
    component.categoricalFilterState = jasmine.createSpyObj('CategoricalFilterState', ['selection']);
    component.categoricalFilterState.selection = jasmine.createSpyObj('CategoricalSelection', ['selection']);
    component.categoricalFilter = jasmine.createSpyObj('CategoricalFilter', ['selection']);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
