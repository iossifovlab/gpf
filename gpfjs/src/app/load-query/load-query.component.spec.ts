import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LoadQueryComponent } from './load-query.component';

describe('LoadQueryComponent', () => {
  let component: LoadQueryComponent;
  let fixture: ComponentFixture<LoadQueryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LoadQueryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoadQueryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
