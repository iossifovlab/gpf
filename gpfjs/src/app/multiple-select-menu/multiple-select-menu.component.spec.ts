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

    fixture = TestBed.createComponent(MultipleSelectMenuComponent);
    component = fixture.componentInstance;
    component.columns = [];
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle checking all', () => {
    component.buttonLabel = 'Uncheck all';
    component.toggleCheckingAll();
    expect(component.buttonLabel).toBe('Check all');
    component.toggleCheckingAll();
    expect(component.buttonLabel).toBe('Uncheck all');
  });
});
