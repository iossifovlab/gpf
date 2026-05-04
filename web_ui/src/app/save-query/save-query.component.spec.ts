import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { APP_BASE_HREF } from '@angular/common';
import { provideHttpClient } from '@angular/common/http';
import { SaveQueryComponent } from './save-query.component';
import { StoreModule } from '@ngrx/store';
import { UsersService } from 'app/users/users.service';
import { ChangeDetectorRef, NO_ERRORS_SCHEMA } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { QueryService } from 'app/query/query.service';
import { NgbModule, NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';

class QueryServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public saveQuery(name: string, desc: string): Observable<object> {
    return of({uuid: '123asd'});
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public saveUserQuery(uuid: string, query_name: string, query_description: string): Observable<object> {
    return of({uuid: '123asd'});
  }

  public getLoadUrl(uuid: string): string {
    return '/' + uuid;
  }
}

describe('SaveQueryComponent', () => {
  let component: SaveQueryComponent;
  let fixture: ComponentFixture<SaveQueryComponent>;
  const queryServiceMock = new QueryServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        StoreModule.forRoot({}),
        NgbModule,
        NgbTooltipModule,
      ],
      declarations: [
        SaveQueryComponent,
      ],
      providers: [
        ConfigService,
        UsersService,
        ChangeDetectorRef,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: QueryService, useValue: queryServiceMock },
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
      schemas: [NO_ERRORS_SCHEMA]
    });

    fixture = TestBed.createComponent(SaveQueryComponent);
    component = fixture.componentInstance;

    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should check if save query button text is changed', fakeAsync(() => {
    component.saveUserQuery('queryName', 'desc');
    expect(component.saveButtonText).toBe('Saved');
    tick(2000);
    expect(component.saveButtonText).toBe('Save');
  }));

  it('should check if input field is focused', () => {
    const focusSpy = jest.spyOn(component.nameInputRef.nativeElement, 'focus');
    const detectChangesSpy = jest.spyOn(component['changeDetectorRef'], 'detectChanges');
    component.focusNameInput();
    expect(focusSpy).toHaveBeenCalledWith();
    expect(detectChangesSpy).toHaveBeenCalledWith();
  });

  it('should close dropdown', () => {
    const isOpenSpy = jest.spyOn(component['dropdown'], 'isOpen').mockReturnValue(true);
    const closeSpy = jest.spyOn(component['dropdown'], 'close');
    component.toggleDropdown();
    expect(isOpenSpy).toHaveBeenCalledWith();
    expect(closeSpy).toHaveBeenCalledWith();
    expect(component.url).toBeNull();
  });

  it('should get uuid when opening dropdown', () => {
    const isOpenSpy = jest.spyOn(component['dropdown'], 'isOpen').mockReturnValue(false);
    const openSpy = jest.spyOn(component['dropdown'], 'open');
    const closeSpy = jest.spyOn(component['dropdown'], 'close');
    component.toggleDropdown();
    expect(isOpenSpy).toHaveBeenCalledWith();
    expect(closeSpy).not.toHaveBeenCalledWith();
    expect(component['urlUUID']).toBe('123asd');
    expect(component.url).toBe('/123asd');
    expect(openSpy).toHaveBeenCalledWith();
  });

  it('should reset url when error in saving query', () => {
    jest.clearAllMocks();
    jest.spyOn(component['dropdown'], 'isOpen').mockReturnValue(false);
    jest.spyOn(queryServiceMock, 'saveQuery').mockImplementation(() => throwError(() => new Error()));
    component.url = '/url';
    component.toggleDropdown();
    expect(component.url).toBeNull();
  });

  it('should not set url when uuid from saving is invalid', () => {
    jest.clearAllMocks();
    jest.spyOn(component['dropdown'], 'isOpen').mockReturnValue(false);
    jest.spyOn(queryServiceMock, 'saveQuery').mockReturnValue(of({uuid: undefined}));
    component.url = '/url';
    component.toggleDropdown();
    expect(component.url).toBe('/url');
  });

  it('should open copied tooltip', fakeAsync(() => {
    const openSpy = jest.spyOn(component.copiedTooltip, 'open');
    const closeSpy = jest.spyOn(component.copiedTooltip, 'close');

    component.openCopiedTooltip();
    expect(openSpy).toHaveBeenCalledWith();
    tick(2000);
    expect(closeSpy).toHaveBeenCalledWith();
  }));
});

