type News = {
    id: string;
    title: string;
    content: string;
    tags: string[];
    createdAt: string; // ISO date string
    hotnessScore: number;
    isConfirmed: boolean;
    sources: string[];
    timeline?: string[]; // Optional array of ISO date strings
}