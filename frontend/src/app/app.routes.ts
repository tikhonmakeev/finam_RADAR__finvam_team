import { Route } from '@angular/router';
import { MainPage } from './components/MainPage/MainPage';
import { NewsPage } from './components/NewsPage/NewsPage';
import { NewsDetailsPage } from './components/NewsDetailsPage/NewsDetailsPage';

export const appRoutes: Route[] = [
    {
        path: '',
        component: MainPage,
        children: [
            {
                path: '',
                component: NewsPage,
            },
            {
                path: 'news/:id',
                component: NewsDetailsPage,
            }
        ]
    }
];
