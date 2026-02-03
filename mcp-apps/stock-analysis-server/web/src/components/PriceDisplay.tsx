import React from "react";

interface PriceDisplayProps {
  price: number;
  change: number;
  changePercent: number;
  size?: "sm" | "md" | "lg";
}

export function PriceDisplay({ price, change, changePercent, size = "md" }: PriceDisplayProps) {
  const isPositive = change >= 0;
  const colorClass = isPositive ? "price-up" : "price-down";

  const sizeClasses = {
    sm: { price: "text-lg", change: "text-xs" },
    md: { price: "text-3xl", change: "text-sm" },
    lg: { price: "text-4xl", change: "text-base" },
  };

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatChange = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}`;
  };

  return (
    <div className="flex flex-col gap-1">
      <div className={`${sizeClasses[size].price} font-semibold text-gray-900 tracking-tight font-mono`}>
        {formatPrice(price)}
      </div>
      <div className={`${sizeClasses[size].change} font-medium ${colorClass} flex items-center gap-2`}>
        <span className="flex items-center gap-1">
          {isPositive ? (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          )}
          {formatChange(change)}
        </span>
        <span>({formatChange(changePercent)}%)</span>
      </div>
    </div>
  );
}
