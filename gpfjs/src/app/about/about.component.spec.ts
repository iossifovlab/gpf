import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AboutComponent } from './about.component';
import { HttpClient, HttpHandler } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';
import { InstanceService } from 'app/instance.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';


class InstanceServiceMock {
  public writeAboutDescription(description: string): Observable<object> {
    return of({
      'content': description
    });
  }

  public getAboutDescription(): Observable<object> {
   return of({
    'content': '# Introduction\n[GPF](https://iossifovlab.com/gpf/) (Genotypes and Phenotypes in Families) is an open-source platform that manages genotypes and phenotypes derived from collections of families.'
    });
  }
}
describe('AboutComponent', () => {
  let component: AboutComponent;
  let fixture: ComponentFixture<AboutComponent>;
  let instanceServiceMock = new InstanceServiceMock();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [AboutComponent],
      providers: [
        HttpClient,
        HttpHandler,
        ConfigService,
        { provide: InstanceService, useValue: instanceServiceMock},
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(AboutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get about description', () => {
    expect(component.aboutDescription).toBe('# Introduction\n[GPF](https://iossifovlab.com/gpf/) (Genotypes and Phenotypes in Families) is an open-source platform that manages genotypes and phenotypes derived from collections of families.');
  });

  it('should write about description', () => {
    jest.spyOn(instanceServiceMock, 'getAboutDescription').mockReturnValueOnce(of({'content': 'new description'}));

    component.writeDescription('new description');
    expect(component.aboutDescription).toBe('new description');
  });
});
