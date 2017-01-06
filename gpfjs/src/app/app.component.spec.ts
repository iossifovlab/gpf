/* tslint:disable:no-unused-variable */

import { TestBed, async } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { MaterialModule } from '@angular/material';
import { PhenotypesComponent } from './phenotypes/phenotypes.component';
import { GenderComponent } from './gender/gender.component';
import { DatasetService } from './dataset/dataset.service';
import { DatasetServiceStub } from './dataset/dataset.service.spec';

describe('AppComponent', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        AppComponent,
        PhenotypesComponent,
        GenderComponent,
      ],
      imports: [
        MaterialModule.forRoot()
      ],
      providers: [
        {
          provide: DatasetService,
          useValue: new DatasetServiceStub(undefined, undefined)
        }
      ]
    });
    TestBed.compileComponents();
  });

  it('should create the app', async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    let app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  }));

  it(`should have as title 'GPF: Genotypes and Phenotypes in Families'`, async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    let app = fixture.debugElement.componentInstance;
    expect(app.title).toEqual(app.title);
  }));

  it('should render title in a h3 tag', async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    let compiled = fixture.debugElement.nativeElement;
    let app = fixture.debugElement.componentInstance;
    expect(compiled.querySelector('h3').textContent).toContain(app.title);
  }));
});
