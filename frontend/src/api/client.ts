const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const AUTH_TOKEN_KEY = "usl_auth_token";

export function getAuthToken(): string {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "dev";
}

export function setAuthToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getAuthToken()}`,
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || "").filter(Boolean).join(", ")
          : data.message || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data as T;
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
  getItem: (itemId: string) => request<UslItemDetailResponse>(`/v1/usl/items/${itemId}`),
  getAdminMatches: () => request<AdminMatchesResponse>("/v1/admin/matches"),
  getPipelineMetrics: () => request<PipelineMetricsResponse>("/v1/admin/pipeline/metrics"),
  getFlags: () => request<FeatureFlagsResponse>("/v1/flags"),
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
    return request<CheckoutRecommendationsResponse>(`/v1/recommendations/checkout${q ? `?${q}` : ""}`);
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
};

export type UslItemUpdate = {
  raw_intent?: string;
  status?: UslItemStatus;
  priority?: number;
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
