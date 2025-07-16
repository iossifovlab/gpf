import { Component, OnInit } from '@angular/core';
import { InstanceService } from 'app/instance.service';
import { switchMap, take } from 'rxjs';

@Component({
    selector: 'gpf-about',
    templateUrl: './about.component.html',
    standalone: false
})
export class AboutComponent implements OnInit {
  public aboutDescription: string;

  public constructor(
    private instanceService: InstanceService,
  ) {}

  public ngOnInit(): void {
    this.instanceService.getAboutDescription().subscribe((res: {content: string}) => {
      this.aboutDescription = res.content;
    });
  }

  public writeDescription(markdown: string): void {
    this.instanceService.writeAboutDescription(markdown).pipe(
      take(1),
      switchMap(() => this.instanceService.getAboutDescription())
    ).subscribe((res: {content: string}) => {
      this.aboutDescription = res.content;
    });
  }
}
