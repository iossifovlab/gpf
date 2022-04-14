import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UniqueFamilyVariantsFilterComponent } from './unique-family-variants-filter.component';
import { NgxsModule } from '@ngxs/store';
import { FormsModule } from '@angular/forms';

describe('UniqueFamilyVariantsFilterComponent', () => {
  let component: UniqueFamilyVariantsFilterComponent;
  let fixture: ComponentFixture<UniqueFamilyVariantsFilterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ UniqueFamilyVariantsFilterComponent ],
      imports: [ NgxsModule.forRoot(), FormsModule ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(UniqueFamilyVariantsFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
