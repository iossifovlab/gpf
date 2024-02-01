import { Component, OnInit } from '@angular/core';
import { AppVersionService } from 'app/app-version.service';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  public gpfVersion = '';
  public gpfjsVersion = environment?.version;

  public constructor(
    private appVersionService: AppVersionService,
  ) {}

  public ngOnInit(): void {
    this.appVersionService.getGpfVersion().subscribe(res => {
      this.gpfVersion = res;
    });
  }
}
