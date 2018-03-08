import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SaveQueryButtonComponent } from './save-query-button.component';

describe('SaveQueryButtonComponent', () => {
  let component: SaveQueryButtonComponent;
  let fixture: ComponentFixture<SaveQueryButtonComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SaveQueryButtonComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SaveQueryButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
