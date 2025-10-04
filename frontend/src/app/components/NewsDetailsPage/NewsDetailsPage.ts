import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ApiService } from '../../service/api-service/api-service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-news-details-page',
  imports: [],
  templateUrl: './NewsDetailsPage.html',
  styleUrl: './NewsDetailsPage.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsDetailsPage implements OnInit {
  private readonly route = inject(ActivatedRoute)
  private readonly apiService = inject(ApiService);

  newsId: string | null = null;
  news = signal<News | null>(null);

  ngOnInit() {
    this.newsId = this.route.snapshot.paramMap.get('id');
    if (this.newsId) {
      this.apiService.getNews(this.newsId).subscribe((news) => {
        this.news.set(news);
        console.log(news);
      });
    }
  }
}
