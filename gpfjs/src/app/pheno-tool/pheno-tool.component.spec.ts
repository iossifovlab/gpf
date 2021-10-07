import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { UsersService } from 'app/users/users.service';
import { PhenoToolComponent } from './pheno-tool.component';
import { PhenoToolService } from './pheno-tool.service';
import { ErrorsState } from 'app/common/errors.state';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { PhenoToolMeasureComponent } from 'app/pheno-tool-measure/pheno-tool-measure.component';
import { MeasuresService } from 'app/measures/measures.service';
import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('PhenoToolComponent', () => {
  let component: PhenoToolComponent;
  let fixture: ComponentFixture<PhenoToolComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolComponent,
        GenesBlockComponent,
        GeneSymbolsComponent,
        PhenoToolMeasureComponent
      ],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: new ActivatedRoute()
        }, DatasetsService, ConfigService, UsersService, FullscreenLoadingService, PhenoToolService, MeasuresService
      ],
      imports: [HttpClientTestingModule, RouterTestingModule,
        NgxsModule.forRoot([ErrorsState, GeneSymbolsState]), NgbNavModule],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
