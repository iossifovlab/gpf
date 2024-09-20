import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { RegionsBlockComponent } from './regions-block.component';
import { regionsFiltersReducer } from 'app/regions-filter/regions-filter.state';
import { StoreModule } from '@ngrx/store';

describe('RegionsBlockComponent', () => {
  let component: RegionsBlockComponent;
  let fixture: ComponentFixture<RegionsBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [RegionsBlockComponent],
      imports: [NgbModule, RouterTestingModule, StoreModule.forRoot({ regionsFilter: regionsFiltersReducer })],
    }).compileComponents();

    fixture = TestBed.createComponent(RegionsBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
