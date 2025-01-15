import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownModule } from 'ngx-markdown';
import { GenomicScoresComponent } from './genomic-scores.component';
import { PopupComponent } from 'app/popup/popup.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { StoreModule } from '@ngrx/store';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';

describe('GenomicScoresComponent', () => {
  let component: GenomicScoresComponent;
  let fixture: ComponentFixture<GenomicScoresComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [
        GenomicScoresComponent,
        PopupComponent,
        ErrorsAlertComponent,
      ],
      imports: [
        NgbModule,
        FormsModule,
        MarkdownModule.forRoot(),
        StoreModule.forRoot({}),
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
      .overrideModule(BrowserDynamicTestingModule, {
        set: {}
      })
      .compileComponents();

    fixture = TestBed.createComponent(GenomicScoresComponent);
    component = fixture.componentInstance;

    component.errors = [];

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
