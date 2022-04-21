import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MultipleSelectMenuComponent } from './multiple-select-menu.component';

describe('MultipleSelectMenuComponent', () => {
  let component: MultipleSelectMenuComponent;
  let fixture: ComponentFixture<MultipleSelectMenuComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [MultipleSelectMenuComponent],
      imports: [FormsModule]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MultipleSelectMenuComponent);
    component = fixture.componentInstance;
    component.columns = [];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle checking all', () => {
    component.buttonLabel = 'Uncheck all';
    component.toggleCheckingAll();
    expect(component.buttonLabel).toEqual('Check all');
    component.toggleCheckingAll();
    expect(component.buttonLabel).toEqual('Uncheck all');
  });
});
