import { useState } from "react";
import { isReliableImageUrl, productImageUrl } from "../../utils/productImage";

type Props = {
  product: {
    sku_id: string;
    product_name: string;
    category: string;
    image_url?: string | null;
  };
  className?: string;
};

export default function ProductImage({ product, className = "w-3/4 object-contain" }: Props) {
  const demoUrl = productImageUrl(product);
  const initial = isReliableImageUrl(product.image_url) ? product.image_url! : demoUrl;
  const [src, setSrc] = useState(initial);

  return (
    <img
      src={src}
      alt={product.product_name}
      className={className}
      loading="lazy"
      onError={() => {
        if (src !== demoUrl) setSrc(demoUrl);
      }}
    />
  );
}
