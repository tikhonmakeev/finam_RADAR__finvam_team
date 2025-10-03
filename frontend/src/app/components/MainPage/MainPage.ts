import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-main-page',
  imports: [RouterModule],
  templateUrl: './MainPage.html',
  styleUrl: './MainPage.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainPage {}
