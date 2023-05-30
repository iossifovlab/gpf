import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DatasetsComponent } from './datasets.component';

describe('DatasetComponent', () => {
  let component: DatasetsComponent;
  let fixture: ComponentFixture<DatasetsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DatasetsComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(DatasetsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it.todo('should create');

  it.todo('check for selectedDataset');
});
