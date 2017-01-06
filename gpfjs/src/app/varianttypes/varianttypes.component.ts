import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css']
})
export class VarianttypesComponent implements OnInit {
  sub: boolean = true;
  ins: boolean = true;
  del: boolean = true;

  constructor() { }

  ngOnInit() {
  }

  selectAll(): void {
    this.sub = true;
    this.ins = true;
    this.del = true;
  }

  selectNone(): void {
    this.sub = false;
    this.ins = false;
    this.del = false;
  }

  getSelectedVarianttypes(): Set<string> {
    let selectedVariantTypes = new Set<string>();
    if (this.sub) {
      selectedVariantTypes.add('sub');
    }
    if (this.ins) {
      selectedVariantTypes.add('ins');
    }
    if (this.del) {
      selectedVariantTypes.add('del');
    }
    return selectedVariantTypes;
  }
}
