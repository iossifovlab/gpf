import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DatasetsComponent } from './datasets.component';

xdescribe('DatasetComponent', () => {
  let component: DatasetsComponent;
  let fixture: ComponentFixture<DatasetsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DatasetsComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DatasetsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('check for selectedDataset', () => {
    expect(component.selectedDataset.id).toEqual('VIP');
  });
});
