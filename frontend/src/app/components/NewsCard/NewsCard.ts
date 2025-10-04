import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { TruncatePipe } from '../../pipes/truncate/truncate-pipe';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-news-card',
  imports: [CommonModule, TruncatePipe, RouterModule],
  templateUrl: './NewsCard.html',
  styleUrl: './NewsCard.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsCard {
  news = input.required<News>();
}
