// services/chat.ts
import { api } from "./api";

export interface ChatResponse {
    enhanced_text: string;
    llm_used: boolean;
    provider: string;
    tokens_used: number;
    estimated_cost: number;
}

export type ChatProvider = "groq" | "gemini";

export async function sendChatMessage(
    query: string,
    ticker?: string,
    provider?: ChatProvider
): Promise<ChatResponse> {
    const res = await api.post<ChatResponse>("/chat", { query, ticker, provider });
    return res.data;
}
