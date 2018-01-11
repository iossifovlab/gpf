import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DatasetDescriptionComponent } from './dataset-description.component';

describe('DatasetDescriptionComponent', () => {
  let component: DatasetDescriptionComponent;
  let fixture: ComponentFixture<DatasetDescriptionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DatasetDescriptionComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DatasetDescriptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
