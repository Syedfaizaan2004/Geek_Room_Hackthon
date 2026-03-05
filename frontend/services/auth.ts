// services/auth.ts
// All field names MUST match the backend schemas exactly:
//   POST /auth/register → { full_name, unique_user_id, date_of_birth }
//   POST /auth/login    → { unique_user_id, date_of_birth }

import { api } from "./api";

export interface UserResponse {
    id: string;
    full_name: string;
    unique_user_id: string;
    created_at: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
}

/** POST /auth/register — backend expects full_name, unique_user_id, date_of_birth */
export async function register(
    full_name: string,
    unique_user_id: string,
    date_of_birth: string
): Promise<UserResponse> {
    const res = await api.post<UserResponse>("/auth/register", {
        full_name,
        unique_user_id,
        date_of_birth,
    });
    return res.data;
}

/** POST /auth/login — backend expects unique_user_id + date_of_birth (DOB is the password) */
export async function login(
    unique_user_id: string,
    date_of_birth: string
): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>("/auth/login", {
        unique_user_id,
        date_of_birth,
    });
    return res.data;
}

/** GET /auth/me */
export async function fetchMe(): Promise<UserResponse> {
    const res = await api.get<UserResponse>("/auth/me");
    return res.data;
}
