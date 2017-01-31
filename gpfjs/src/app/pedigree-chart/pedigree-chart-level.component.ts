import { Input, Component, OnInit } from '@angular/core';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';

class PedigreeDataWithPosition  {
  constructor(
    public pedigreeData: PedigreeData,
    public xCenter: number,
    public yCenter: number,
    public size: number,
    public scaleFactor: number
  ) { }
  
  get xUpperLeftCorner() {
    return this.xCenter - this.size / 2;
  }
  
  get yUpperLeftCorner() {
    return this.yCenter - this.size / 2;
  }
}

class Line { 
  constructor(
    public startX: number,
    public startY: number,
    public endX: number,
    public endY: number
  ) { }
}

@Component({
  selector: '[gpf-pedigree-chart-level]',
  templateUrl: './pedigree-chart-level.component.html'
})
export class PedigreeChartLevelComponent implements OnInit {
  pedigreeDataWithLayout: PedigreeDataWithPosition[];
  lines: Line[];
  
  @Input() connectingLineYPosition: number;
  @Input() pedigreeData: PedigreeData[];
  
  
  ngOnInit() {
    this.pedigreeDataWithLayout = this.generateLayout(this.pedigreeData);
    this.lines = this.generateLines(this.pedigreeDataWithLayout, this.connectingLineYPosition);
  }

  
  private generateLayout(pedigreeData: PedigreeData[], member_size = 21, width = 100,  max_gap = 8, total_height=30) {
    let pedigreeDataWithPositions = new Array<PedigreeDataWithPosition>(); 
    let num_elements = pedigreeData.length;
    let totalWidth = member_size * num_elements + max_gap * (num_elements - 1);
    let scaleFactor: number;
    let x_offset = 0;
    
    if (totalWidth > width) {
      scaleFactor = width / totalWidth;
    }
    else {
      scaleFactor = 1.0;
      x_offset = (width - totalWidth) / 2;
    }
    
    let size = scaleFactor * member_size;
    let gap = scaleFactor * max_gap;
    let y_center = total_height / 2;
    
    let x_center = x_offset + size/2;
    
    for(let element of pedigreeData) {
      pedigreeDataWithPositions.push(new PedigreeDataWithPosition(element, x_center, y_center, size, scaleFactor));
      x_center += size + gap;
    }
    return pedigreeDataWithPositions;
    
  }
  
  private generateLines(pedigreeData: PedigreeDataWithPosition[], line_y = 50) {
    let lines = new Array<Line>();
  
    let start_x = pedigreeData[0].xCenter;
    let end_x = pedigreeData[pedigreeData.length - 1].xCenter;
    
    if (start_x != end_x) {
      lines.push(new Line(start_x, line_y, end_x, line_y));
    }
    
    for(let element of pedigreeData) {
      if (element.yCenter != line_y) {
        lines.push(new Line(element.xCenter, element.yCenter, element.xCenter, line_y));
      }
    }
    
    return lines;
  }
}

