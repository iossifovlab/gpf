import { Component, OnInit } from '@angular/core';
import { UsersService } from 'app/users/users.service';
import { FederationCredential } from './federation-credentials';

@Component({
  selector: 'gpf-federation-credentials',
  templateUrl: './federation-credentials.component.html',
  styleUrls: ['./federation-credentials.component.css']
})
export class FederationCredentialsComponent implements OnInit {
  public credentials: FederationCredential[];

  public constructor(
    private usersService: UsersService
  ) {}

  public ngOnInit(): void {
    this.usersService.getFederationCredentials().subscribe(res => {
      this.credentials = res;
      console.log(this.credentials);
    });
  }
}
