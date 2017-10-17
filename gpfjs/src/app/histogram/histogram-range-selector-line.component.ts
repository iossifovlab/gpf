import { Input, Component, OnInit, ViewChild, ViewChildren, ViewEncapsulation, Output, EventEmitter, SimpleChanges, QueryList } from '@angular/core';
import * as d3 from 'd3';

@Component({
  encapsulation: ViewEncapsulation.None,
  selector: '[gpf-histogram-range-selector-line]',
  templateUrl: './histogram-range-selector-line.component.html',
  styleUrls: ['./histogram-range-selector-line.component.css']
})
export class HistogramRangeSelectorLineComponent {
  @Input() y = 10;
  @Input() height = 90;

  @Input() minX: number;
  @Input() maxX: number;

  @ViewChild('draggable') draggable: any;
  @ViewChildren('triangle') triangles: QueryList<any>;

  @Input() text: string;
  @Input() textOnRight: boolean = true;

  @Input() scale: any;
  @Input() index = 0;
  @Output() indexChange = new EventEmitter();

  ngOnInit() {
    d3.select(this.draggable.nativeElement).
      call(d3.drag().on("drag", () => this.onDrag(d3.event.x)))
  }

  ngAfterViewInit() {
    this.triangles.forEach((triangle) => {
      d3.select(triangle.nativeElement).attr("d", d3.symbol().type((d3.symbolTriangle)));
    })
  }

  onDrag(newPositionX) {
      for(var i  = 1; i < this.scale.domain().length; i++) {
          var prev_val = (i - 1) * this.scale.step()
          var curr_val = i * this.scale.step()
          if (curr_val> newPositionX) {
              var prev = Math.abs(newPositionX - prev_val)
              var curr = Math.abs(newPositionX - curr_val)
              this.index = prev < curr ? i - 1 : i;
              this.indexChange.emit(this.index);
              break;
          }
      }
  }

  get x() {
      return this.scale.step() * this.index;
  }
}
