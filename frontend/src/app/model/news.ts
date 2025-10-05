type Source = {
    url: string;
    addedAt: string; // ISO date string
}

type News = {
    id: number | string;
    title: string;
    content: string;
    tags: string[];
    createdAt: string; // ISO date string
    updatedAt: string; // ISO date string
    hotnessScore: number;
    isConfirmed: boolean;
    sources: Source[];
}