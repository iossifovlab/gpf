import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { RegionsBlockComponent } from './regions-block.component';
import { regionsFiltersReducer, resetRegionsFilters } from 'app/regions-filter/regions-filter.state';
import { Store, StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { InstanceService } from 'app/instance.service';
import { Observable, of } from 'rxjs';

class InstanceServiceMock {
  public getGenome(): Observable<string> {
    return of('hg38');
  }
}

describe('RegionsBlockComponent', () => {
  let component: RegionsBlockComponent;
  let fixture: ComponentFixture<RegionsBlockComponent>;
  let store: Store;
  const instanceServiceMock = new InstanceServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [RegionsBlockComponent],
      imports: [
        NgbModule,
        RouterTestingModule,
        StoreModule.forRoot({ regionsFilter: regionsFiltersReducer })
      ],
      providers: [
        ConfigService,
        provideHttpClient(),
        { provide: InstanceService, useValue: instanceServiceMock},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RegionsBlockComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    fixture.detectChanges();

    // Mock ngbNav ViewChild
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    component.ngbNav = {
      activeId: undefined,
      select: jest.fn()
    } as any;
  }));

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get genome', () => {
    component.ngOnInit();
    expect(component.genome).toBe('hg38');
  });

  it('should open regions tab if there is saved state', () => {
    jest.useFakeTimers();
    jest.spyOn(store, 'select').mockReturnValue(of(['region1', 'region2']));

    component.ngAfterViewInit();
    jest.advanceTimersByTime(100);

    expect(component.ngbNav.select).toHaveBeenCalledWith('regionsFilter');
  });

  it('should reset typed regions when tab changes', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.onNavChange();
    expect(dispatchSpy).toHaveBeenCalledWith(resetRegionsFilters());
  });
});
