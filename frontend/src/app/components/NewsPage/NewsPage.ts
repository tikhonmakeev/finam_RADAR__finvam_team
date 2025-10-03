import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-news-page',
  imports: [],
  templateUrl: './NewsPage.html',
  styleUrl: './NewsPage.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsPage {}
