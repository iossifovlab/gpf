import {
  Input, Component, OnInit, AfterViewInit, ViewChild, ViewChildren,
  ViewEncapsulation, Output, EventEmitter, QueryList, ElementRef
} from '@angular/core';
import * as d3 from 'd3';

@Component({
    encapsulation: ViewEncapsulation.None,
    selector: '[gpf-histogram-range-selector-line]',
    templateUrl: './histogram-range-selector-line.component.html',
    styleUrls: ['./histogram-range-selector-line.component.css'],
    standalone: false
})
export class HistogramRangeSelectorLineComponent implements OnInit, AfterViewInit {
  @Input() public y = 10;
  @Input() public height = 90;

  @Input() public minX: number;
  @Input() public maxX: number;

  @ViewChild('draggable', {static: true}) public draggable: ElementRef;
  @ViewChildren('triangle') public triangles: QueryList<ElementRef>;

  @Input() public text: string;
  @Input() public textOnRight = true;

  @Input() public width: number;
  @Input() public x = 0;
  @Output() public xChange = new EventEmitter();

  public ngOnInit(): void {
    d3.select(this.draggable.nativeElement as HTMLElement).
      call(d3.drag().on('drag', (event: any, d) => this.onDrag(event.x)));
  }

  public ngAfterViewInit(): void {
    this.triangles.forEach((triangle) => {
      d3.select(triangle.nativeElement)
        .attr('d', d3.symbol().type(d3.symbolTriangle));
    });
  }

  private onDrag(newPositionX): void {
    this.xChange.emit(newPositionX);
  }
}
