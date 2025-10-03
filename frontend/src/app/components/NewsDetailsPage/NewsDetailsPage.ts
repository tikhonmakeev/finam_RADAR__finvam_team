import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-news-details-page',
  imports: [],
  templateUrl: './NewsDetailsPage.html',
  styleUrl: './NewsDetailsPage.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsDetailsPage {}
