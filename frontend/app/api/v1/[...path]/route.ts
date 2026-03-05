import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const METHOD_WITHOUT_BODY = new Set(["GET", "HEAD", "OPTIONS"]);

function normalizeBackendBase(raw?: string | null): string | null {
    if (!raw) return null;
    let url = raw.trim();
    if (!url) return null;

    if (!/^https?:\/\//i.test(url)) {
        url = `https://${url}`;
    }

    url = url.replace(/\/+$/, "");
    if (!/\/api\/v1$/i.test(url)) {
        url = `${url}/api/v1`;
    }
    return url;
}

function deriveBackendFromHost(host: string): string | null {
    const normalizedHost = host.split(":")[0].trim();
    if (!normalizedHost) return null;

    if (normalizedHost === "localhost" || normalizedHost === "127.0.0.1") {
        return "http://localhost:8000/api/v1";
    }

    const candidates = [
        normalizedHost.replace("-frontend", "-backend"),
        normalizedHost.replace(/^frontend\./i, "backend."),
        normalizedHost.replace(/^app\./i, "api."),
    ].filter((value, index, all) => value && value !== normalizedHost && all.indexOf(value) === index);

    if (candidates.length === 0) return null;
    return `https://${candidates[0]}/api/v1`;
}

function resolveBackendBase(request: NextRequest): string | null {
    const envCandidates = [
        process.env.BACKEND_URL,
        process.env.API_BASE_URL,
        process.env.NEXT_PUBLIC_API_URL,
        process.env.NEXT_PUBLIC_BACKEND_URL,
    ];

    for (const candidate of envCandidates) {
        const normalized = normalizeBackendBase(candidate);
        if (normalized) return normalized;
    }

    const hostHeader = request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? "";
    return normalizeBackendBase(deriveBackendFromHost(hostHeader));
}

function buildTargetUrl(base: string, pathParts: string[], search: string): string {
    const cleanBase = base.replace(/\/+$/, "");
    const cleanPath = pathParts
        .map((segment) => encodeURIComponent(segment))
        .join("/");
    return `${cleanBase}/${cleanPath}${search}`;
}

function buildForwardHeaders(request: NextRequest): Headers {
    const headers = new Headers();
    for (const [key, value] of request.headers.entries()) {
        const lower = key.toLowerCase();
        if (lower === "host" || lower === "content-length" || lower === "connection") {
            continue;
        }
        headers.set(key, value);
    }
    return headers;
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const backendBase = resolveBackendBase(request);
    if (!backendBase) {
        return Response.json(
            {
                success: false,
                error: "Backend target unresolved",
                detail: "Set BACKEND_URL or NEXT_PUBLIC_API_URL for the frontend service.",
            },
            { status: 500 },
        );
    }

    const { path } = await context.params;
    const targetUrl = buildTargetUrl(backendBase, path, request.nextUrl.search);
    const headers = buildForwardHeaders(request);
    const method = request.method.toUpperCase();

    let body: BodyInit | undefined;
    if (!METHOD_WITHOUT_BODY.has(method)) {
        const raw = await request.arrayBuffer();
        if (raw.byteLength > 0) {
            body = raw;
        }
    }

    let upstream: Response;
    try {
        upstream = await fetch(targetUrl, {
            method,
            headers,
            body,
            redirect: "manual",
            cache: "no-store",
        });
    } catch (error) {
        return Response.json(
            {
                success: false,
                error: "Backend request failed",
                detail: error instanceof Error ? error.message : "Unknown network error",
            },
            { status: 502 },
        );
    }

    const responseHeaders = new Headers();
    for (const [key, value] of upstream.headers.entries()) {
        if (key.toLowerCase() === "content-length") continue;
        responseHeaders.set(key, value);
    }

    return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: responseHeaders,
    });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    return proxy(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    return proxy(request, context);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    return proxy(request, context);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    return proxy(request, context);
}

export async function OPTIONS(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    return proxy(request, context);
}
