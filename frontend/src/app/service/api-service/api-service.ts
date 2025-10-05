import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://158.160.195.186/api';

  getAllNews(filters?: {
    tags: string[];
    onlyVerified: boolean;
  }): Observable<News[]> {
    let apiUrl = `${this.baseUrl}/news`;
    if (!filters) {
      return this.http.get<News[]>(apiUrl);
    }

    const tags = filters.tags || [];
    const onlyVerified = filters.onlyVerified || false;

    const tagsString = tags.length > 0 ? `tags=${tags.join(',')}` : '';
    const verifiedString = onlyVerified ? 'onlyConfirmed=true' : '';

    const queryParams = [tagsString, verifiedString]
      .filter((param) => param !== '')
      .join('&');

    apiUrl += queryParams ? `?${queryParams}` : '';

    return this.http.get<News[]>(apiUrl);
  }

  getNews(id: string): Observable<News> {
    const apiUrl = `${this.baseUrl}/news/${id}`;
    return this.http.get<News>(apiUrl);
  }
}
