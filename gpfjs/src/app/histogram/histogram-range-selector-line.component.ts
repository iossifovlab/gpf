import {
  Input, Component, OnInit, AfterViewInit, ViewChild, ViewChildren,
  ViewEncapsulation, Output, EventEmitter, SimpleChanges, QueryList
} from '@angular/core';
import * as d3 from 'd3';

@Component({
  encapsulation: ViewEncapsulation.None,
  selector: '[gpf-histogram-range-selector-line]',
  templateUrl: './histogram-range-selector-line.component.html',
  styleUrls: ['./histogram-range-selector-line.component.css']
})
export class HistogramRangeSelectorLineComponent implements OnInit, AfterViewInit {
  @Input() y = 10;
  @Input() height = 90;

  @Input() minX: number;
  @Input() maxX: number;

  @ViewChild('draggable') draggable: any;
  @ViewChildren('triangle') triangles: QueryList<any>;

  @Input() text: string;
  @Input() textOnRight = true;

  @Input() width: any;
  @Input() x = 0;
  @Output() xChange = new EventEmitter();

  ngOnInit() {
    d3.select(this.draggable.nativeElement).
      call(d3.drag().on('drag', () => this.onDrag(d3.event.x)));
  }

  ngAfterViewInit() {
    this.triangles.forEach((triangle) => {
      d3.select(triangle.nativeElement)
        .attr('d', d3.symbol().type((d3.symbolTriangle)));
    });
  }

  onDrag(newPositionX) {
      this.xChange.emit(newPositionX);
  }
}
