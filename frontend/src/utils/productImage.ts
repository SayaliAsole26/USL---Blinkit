const CATEGORY_COLORS: Record<string, string> = {
  Groceries: "16a34a",
  "Personal Care": "0d9488",
  Electronics: "2563eb",
  "Pet Supplies": "d97706",
  "Home Essentials": "7c3aed",
  "Health & Nutrition": "dc2626",
  Gifting: "db2777",
};

type ProductLike = {
  sku_id: string;
  product_name: string;
  category: string;
  image_url?: string | null;
};

/** Reliable demo image per product (category-colored avatar). */
export function productImageUrl(product: ProductLike): string {
  const label = product.product_name
    .replace(/[^a-zA-Z0-9 ]/g, " ")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .join(" ");
  const bg = CATEGORY_COLORS[product.category] ?? "64748b";
  const name = encodeURIComponent(label || product.sku_id);
  return `https://ui-avatars.com/api/?name=${name}&size=200&background=${bg}&color=fff&bold=true&format=png`;
}

export function isReliableImageUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  return !url.includes("placehold.co");
}
