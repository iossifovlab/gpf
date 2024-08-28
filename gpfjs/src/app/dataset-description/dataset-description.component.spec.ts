import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Component, OnInit } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { MarkdownService } from 'ngx-markdown';
import { DatasetDescriptionComponent } from './dataset-description.component';
import { APP_BASE_HREF } from '@angular/common';
import { StoreModule } from '@ngrx/store';

class MarkdownServiceMock {
  public compile = (): void => null;
  public getSource = (): void => null;
  public highlight = (): void => null;
  public renderKatex = (): void => null;
}

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
class MockDatasetDescriptionComponent extends DatasetDescriptionComponent implements OnInit {
  public ngOnInit(): void {
    return null;
  }
}

describe('DatasetDescriptionComponent', () => {
  let component: MockDatasetDescriptionComponent;
  let fixture: ComponentFixture<MockDatasetDescriptionComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MockDatasetDescriptionComponent],
      providers: [
        {provide: ActivatedRoute, useValue: new ActivatedRoute()},
        DatasetsService,
        UsersService,
        ConfigService,
        {provide: MarkdownService, useClass: MarkdownServiceMock},
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [RouterTestingModule, HttpClientTestingModule, StoreModule.forRoot({})]
    }).compileComponents();

    fixture = TestBed.createComponent(MockDatasetDescriptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
