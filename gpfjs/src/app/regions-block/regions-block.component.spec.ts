import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { RegionsBlockComponent } from './regions-block.component';
import { RegionsFilterState } from 'app/regions-filter/regions-filter.state';

describe('RegionsBlockComponent', () => {
  let component: RegionsBlockComponent;
  let fixture: ComponentFixture<RegionsBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [RegionsBlockComponent],
      imports: [NgbModule, RouterTestingModule, NgxsModule.forRoot([RegionsFilterState], {developmentMode: true})],
    }).compileComponents();

    fixture = TestBed.createComponent(RegionsBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
