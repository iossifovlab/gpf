import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css']
})
export class GenderComponent implements OnInit {
  male: boolean = true;
  female: boolean = true;

  constructor() { }

  ngOnInit() {
  }

  selectAll(): void {
    this.male = true;
    this.female = true;
  }

  selectNone(): void {
    this.male = false;
    this.female = false;
  }

  getSelectedGenders(): Set<string> {
    let selectedGenders = new Set<string>();
    if (this.male) {
      selectedGenders.add('male');
    }
    if (this.female) {
      selectedGenders.add('female');
    }
    return selectedGenders;
  }

}
