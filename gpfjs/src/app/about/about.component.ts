import { Component, OnInit } from '@angular/core';
import { InstanceService } from 'app/instance.service';
import { switchMap, take } from 'rxjs';

@Component({
  selector: 'gpf-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.css']
})
export class AboutComponent implements OnInit {
  public aboutDescription: string;

  public constructor(
    private instanceService: InstanceService,
  ) {}

  public ngOnInit(): void {
    this.instanceService.getAboutDescription().subscribe((res: {description: string}) => {
      this.aboutDescription = res.description;
    });
  }

  public writeDescription(markdown: string): void {
    this.instanceService.writeAboutDescription(markdown).pipe(
      take(1),
      switchMap(() => this.instanceService.getAboutDescription())
    ).subscribe((res: {description: string}) => {
      this.aboutDescription = res.description;
    });
  }
}
