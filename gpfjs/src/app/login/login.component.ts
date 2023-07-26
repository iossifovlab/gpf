import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'gpf-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  public constructor(
    private router: Router
  ) {}

  public ngOnInit() {
    const url = new URL(window.location.href);
    let state = url.searchParams.get('state');
    let redirectTo = ['datasets'];
    if (state) {
      state = JSON.parse(atob(state));
      if (state['came_from']) {
        redirectTo = [state['came_from']];
      }
    }
    this.router.navigate(redirectTo);
  }
}
