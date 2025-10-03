import { TuiRoot } from "@taiga-ui/core";
import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';

@Component({
  imports: [RouterModule, TuiRoot],
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.less',
})
export class App {
  protected title = 'frontend';
}
