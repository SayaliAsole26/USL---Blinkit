/** Strip trailing slashes and accidental `/v1` suffix (common Vercel misconfig). */
export function normalizeApiBaseUrl(raw: string): string {
  let url = raw.trim().replace(/\/+$/, "");
  if (url.endsWith("/v1")) {
    url = url.slice(0, -3);
  }
  return url;
}

const API_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_URL || "http://localhost:8000");
const USER_ID_KEY = "usl_user_id";

export function getApiBaseUrl(): string {
  return API_URL;
}

/** One unique user per browser — each gets their own USL in the backend. */
export function ensureUserSession(): string {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(USER_ID_KEY, userId);
    localStorage.removeItem("usl_welcome_seen");
  }
  return userId;
}

export function getAuthToken(): string {
  return ensureUserSession();
}

export function resetUserSession(): string {
  const userId = crypto.randomUUID();
  localStorage.setItem(USER_ID_KEY, userId);
  return userId;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

const REQUEST_TIMEOUT_MS = 45_000;
const CHECKOUT_REQUEST_TIMEOUT_MS = 90_000;

async function requestOnce<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getAuthToken()}`,
        ...options.headers,
      },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        `API at ${API_URL} timed out after ${timeoutMs / 1000}s (Railway may be waking up). Try again.`
      );
    }
    throw new Error(
      `Cannot reach API at ${API_URL}. Check VITE_API_URL on Vercel, Railway backend health, and CORS_ORIGINS.`
    );
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail;
    let message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || "").filter(Boolean).join(", ")
          : data.message || `Request failed (${response.status})`;

    if (response.status === 404 && message === "Not Found") {
      message =
        `API route not found at ${API_URL}${path}. ` +
        "Check VITE_API_URL on Vercel (Railway URL only, no /v1 suffix) and redeploy.";
    }

    throw new Error(message);
  }

  return data as T;
}

/** Retry transient network failures (e.g. Railway cold start). */
async function request<T>(
  path: string,
  options: RequestInit = {},
  retries = 4,
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await requestOnce<T>(path, options, timeoutMs);
    } catch (err) {
      lastError = err;
      const message = err instanceof Error ? err.message : "";
      const retryable =
        message.includes("Cannot reach API") ||
        message.includes("timed out") ||
        message.includes("Failed to fetch");
      if (retryable && attempt < retries) {
        await sleep(800 * (attempt + 1));
        continue;
      }
      throw err;
    }
  }
  throw lastError;
}

/** Wake Railway / confirm API is reachable before mutating requests. */
export async function warmupApi(): Promise<boolean> {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 15_000);
      const response = await fetch(`${API_URL}/health`, { signal: controller.signal });
      window.clearTimeout(timeoutId);
      if (response.ok) return true;
    } catch {
      await sleep(1000 * (attempt + 1));
    }
  }
  return false;
}

export const api = {
  getLocation: () => request<LocationResponse>("/v1/users/location"),
  setLocation: (body: LocationCreate) =>
    request<LocationResponse>("/v1/users/location", { method: "POST", body: JSON.stringify(body) }),
  listItems: (status?: StatusFilter) => {
    const query = status && status !== "all" ? `?status=${status}` : status === "all" ? "?status=all" : "";
    return request<UslItemListResponse>(`/v1/usl/items${query}`);
  },
  createItem: (body: UslItemCreate) =>
    request<UslItemResponse>("/v1/usl/items", { method: "POST", body: JSON.stringify(body) }),
  updateItem: (itemId: string, body: UslItemUpdate) =>
    request<UslItemResponse>(`/v1/usl/items/${itemId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteItem: (itemId: string) => request<void>(`/v1/usl/items/${itemId}`, { method: "DELETE" }),
  watchItemAvailability: (itemId: string) =>
    request<AvailabilityWatchResponse>(`/v1/usl/items/${itemId}/watch`, { method: "POST" }),
  getAvailabilityNotifications: () =>
    request<AvailabilityNotificationsResponse>("/v1/usl/availability-notifications"),
  getItem: (itemId: string) => request<UslItemDetailResponse>(`/v1/usl/items/${itemId}`),
  getAdminMatches: () => request<AdminMatchesResponse>("/v1/admin/matches"),
  getPipelineMetrics: () => request<PipelineMetricsResponse>("/v1/admin/pipeline/metrics"),
  getFlags: () => request<FeatureFlagsResponse>("/v1/flags"),
  listCatalogProducts: (params?: { category?: string; q?: string; pincode?: string }) => {
    const search = new URLSearchParams();
    if (params?.category) search.set("category", params.category);
    if (params?.q) search.set("q", params.q);
    if (params?.pincode) search.set("pincode", params.pincode);
    const q = search.toString();
    return request<CatalogProductsResponse>(`/v1/integrations/catalog/products${q ? `?${q}` : ""}`);
  },
  getCart: () => request<CartResponse>("/v1/integrations/cart"),
  addCartItem: (skuId: string, quantity = 1) =>
    request<{ ok: boolean; sku_id: string }>("/v1/integrations/cart/items", {
      method: "POST",
      body: JSON.stringify({ sku_id: skuId, quantity }),
    }),
  getCheckoutRecommendations: (cartSkus?: string) => {
    const params = new URLSearchParams();
    if (cartSkus) params.set("cart_skus", cartSkus);
    const q = params.toString();
    return request<CheckoutRecommendationsResponse>(
      `/v1/recommendations/checkout${q ? `?${q}` : ""}`,
      {},
      2,
      CHECKOUT_REQUEST_TIMEOUT_MS,
    );
  },
  recommendationAction: (recId: string, action: RecommendationActionType, checkoutSessionId: string) =>
    request<RecommendationActionResponse>(`/v1/recommendations/${recId}/actions`, {
      method: "POST",
      body: JSON.stringify({ action, checkout_session_id: checkoutSessionId }),
    }),
  completeOrder: (orderId: string, skuIds: string[]) =>
    request<OrderCompletedResponse>("/v1/integrations/orders/completed", {
      method: "POST",
      body: JSON.stringify({ order_id: orderId, sku_ids: skuIds }),
    }),
  getCheckoutContext: () => request<CheckoutContextResponse>("/v1/context/checkout"),
};

export type LocationCreate = {
  city: string;
  state: string;
  pincode: string;
};

export type LocationResponse = LocationCreate & {
  updated_at: string;
};

export type UslItemStatus = "pending" | "saved_for_later" | "dismissed" | "purchased";

export type StatusFilter = "pending" | "purchased" | "all";

export type UslItemCreate = {
  raw_intent: string;
  priority?: number;
  event_date?: string | null;
};

export type UslItemUpdate = {
  raw_intent?: string;
  status?: UslItemStatus;
  priority?: number;
  event_date?: string | null;
};

export type CatalogMatchResponse = {
  match_id: string;
  sku_id: string;
  product_name: string | null;
  category: string | null;
  price: number | null;
  image_url: string | null;
  match_confidence: number;
  availability_status: string;
  pincode: string;
  rank: number;
  matched_at: string;
};

export type UslItemResponse = {
  item_id: string;
  raw_intent: string;
  normalized_name: string | null;
  category: string | null;
  status: UslItemStatus;
  match_status: MatchStatus;
  priority: number | null;
  event_date: string | null;
  created_at: string;
  updated_at: string;
  purchased_at: string | null;
  catalog_matches: CatalogMatchResponse[];
};

export type UslItemDetailResponse = UslItemResponse & {
  metadata: {
    shortlist_size: number | null;
    processing_latency_ms: number | null;
    intent_confidence: number | null;
    last_error: string | null;
  } | null;
};

export type MatchStatus = "queued" | "processing" | "matched" | "unmatched";

export type AdminMatchesResponse = {
  items: Array<{
    item_id: string;
    raw_intent: string;
    normalized_name: string | null;
    match_status: MatchStatus;
    shortlist_size: number | null;
    processing_latency_ms: number | null;
    matches: Array<{ sku_id: string; confidence: number; availability_status: string; rank: number }>;
  }>;
};

export type PipelineMetricsResponse = {
  path_a: {
    runs: number;
    avg_shortlist_size: number;
    max_llm_candidate_size: number;
    avg_processing_latency_ms: number;
  };
  path_b: {
    runs: number;
    avg_shortlist_size: number;
    max_llm_candidate_size: number;
    avg_output_count: number;
    avg_processing_latency_ms: number;
  };
};

export type UslItemListResponse = {
  items: UslItemResponse[];
  total: number;
};

export type FeatureFlagsResponse = {
  usl_enabled: boolean;
  usl_checkout_recommendations: boolean;
  experiments_enabled?: boolean;
  rollout_percentage?: number;
};

export type AvailabilityWatchResponse = {
  watch_id: string;
  item_id: string;
  sku_id: string;
  pincode: string;
  message: string;
};

export type AvailabilityNotificationsResponse = {
  count: number;
  notifications: Array<{
    watch_id: string;
    item_id: string;
    sku_id: string;
    message: string;
  }>;
};

export type CatalogProduct = {
  sku_id: string;
  product_name: string;
  category: string;
  price: number;
  image_url: string | null;
};

export type CatalogProductsResponse = {
  count: number;
  products: CatalogProduct[];
};

export type CartResponse = {
  items: Array<{ sku_id: string; quantity: number }>;
};

export type CheckoutRecommendation = {
  recommendation_id: string;
  usl_item_id: string;
  sku_id: string;
  product_name: string;
  price: number;
  image_url: string | null;
  reason_type: string;
  reason_text: string;
  confidence: number;
};

export type CheckoutRecommendationsResponse = {
  checkout_session_id: string;
  recommendations: CheckoutRecommendation[];
  shortlist_size: number;
  latency_ms: number;
};

export type RecommendationActionType = "added_to_cart" | "saved_for_later" | "dismissed";

export type RecommendationActionResponse = {
  recommendation_id: string;
  action: RecommendationActionType;
  usl_item_id: string | null;
  sku_id: string;
  message: string;
};

export type OrderCompletedResponse = {
  order_id: string;
  usl_items_marked_purchased: number;
};

export type CheckoutContextResponse = {
  season: string;
  season_label: string;
  weather: {
    forecast: string;
    severity: string;
    days_ahead: number | null;
    max_precipitation_mm?: number | null;
  };
  cart_categories: string[];
  upcoming_events: Array<{
    item_id: string;
    event_date: string;
    days_until: number;
    label: string;
  }>;
  festival: string | null;
};
