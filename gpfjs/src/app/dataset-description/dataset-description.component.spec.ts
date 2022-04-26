import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Component } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { DatasetDescriptionComponent } from './dataset-description.component';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class MockDatasetDescriptionComponent extends DatasetDescriptionComponent {
  public ngOnInit(): void {
    return null;
  }
}

describe('DatasetDescriptionComponent', () => {
  let component: MockDatasetDescriptionComponent;
  let fixture: ComponentFixture<MockDatasetDescriptionComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [MockDatasetDescriptionComponent],
      providers: [
        {provide: ActivatedRoute, useValue: new ActivatedRoute()},
        DatasetsService,
        UsersService,
        ConfigService,
      ],
      imports: [RouterTestingModule, HttpClientTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MockDatasetDescriptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
