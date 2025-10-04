import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NewsCard } from '../NewsCard/NewsCard';
import { TuiScrollbar, TuiScrollable } from '@taiga-ui/core';

@Component({
  selector: 'app-news-page',
  imports: [CommonModule, NewsCard, TuiScrollbar, TuiScrollable],
  templateUrl: './NewsPage.html',
  styleUrl: './NewsPage.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsPage {
  readonly newsList: News[] = [
  {
    id: "1",
    title: "Запуск новой версии искусственного интеллекта от ведущей компании",
    content: "Сегодня состоялся релиз обновленной версии ИИ-системы, которая демонстрирует революционные возможности в обработке естественного языка и генерации контента.",
    tags: ["технологии", "искусственный интеллект", "инновации"],
    createdAt: "2024-01-15T10:30:00.000Z",
    hotnessScore: 100,
    isConfirmed: true,
    sources: ["https://technews.com/ai-launch", "https://innovation.org/update"],
    timeline: ["2024-01-10T09:00:00.000Z", "2024-01-14T15:20:00.000Z"]
  },
  {
    id: "2",
    title: "Прорыв в квантовых вычислениях: достигнута новая веха",
    content: "Ученые объявили о значительном прогрессе в области квантовых компьютеров, увеличив стабильность кубитов в 5 раз по сравнению с предыдущими показателями.",
    tags: ["наука", "квантовые вычисления", "технологии"],
    createdAt: "2024-01-14T14:45:00.000Z",
    hotnessScore: 88,
    isConfirmed: true,
    sources: ["https://sciencejournal.org/quantum", "https://research.edu/breakthrough"]
  },
  {
    id: "3",
    title: "Кибератака на крупный финансовый институт: детали инцидента",
    content: "В результате сложной кибератаки пострадали системы одного из крупнейших банков. Эксперты работают над восстановлением и расследованием происшествия.",
    tags: ["кибербезопасность", "финансы", "происшествия"],
    createdAt: "2024-01-15T08:15:00.000Z",
    hotnessScore: 50,
    isConfirmed: false,
    sources: ["https://securitywatch.com/incident", "https://finance-news.net/attack"],
    timeline: ["2024-01-14T22:30:00.000Z", "2024-01-15T02:45:00.000Z", "2024-01-15T07:00:00.000Z"]
  },
  {
    id: "4",
    title: "Революционное открытие в медицине: новый метод лечения онкологии",
    content: "Исследовательская группа представила инновационный подход к терапии раковых заболеваний, показавший эффективность 85% в клинических испытаниях.",
    tags: ["медицина", "онкология", "здоровье"],
    createdAt: "2024-01-13T11:20:00.000Z",
    hotnessScore: 32,
    isConfirmed: true,
    sources: ["https://medicalbreakthroughs.org/cancer", "https://health-research.edu/therapy"]
  },
  {
    id: "5",
    title: "Климатический саммит: мировые лидеры договорились о новых обязательствах",
    content: "По итогам экстренного климатического саммита принята резолюция с конкретными целями по сокращению выбросов и переходу на зеленую энергетику.",
    tags: ["экология", "политика", "климат"],
    createdAt: "2024-01-15T16:00:00.000Z",
    hotnessScore: 84,
    isConfirmed: true,
    sources: ["https://climate-news.net/summit", "https://global-politics.org/agreement"],
    timeline: ["2024-01-14T10:00:00.000Z", "2024-01-15T09:30:00.000Z"]
  }
];
}
