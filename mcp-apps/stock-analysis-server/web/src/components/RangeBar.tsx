import React from "react";

interface RangeBarProps {
  low: number;
  high: number;
  current: number;
  label?: string;
}

export function RangeBar({ low, high, current, label }: RangeBarProps) {
  const range = high - low;
  const position = range > 0 ? ((current - low) / range) * 100 : 50;

  return (
    <div className="space-y-2">
      {label && (
        <div className="flex justify-between text-xs text-gray-500">
          <span>{label}</span>
        </div>
      )}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-gray-600 w-16 text-right font-mono">
          ${low.toFixed(2)}
        </span>
        <div className="flex-1 range-bar">
          <div className="range-bar-fill" style={{ width: "100%" }} />
          <div className="range-bar-marker" style={{ left: `${Math.min(100, Math.max(0, position))}%` }} />
        </div>
        <span className="text-xs font-medium text-gray-600 w-16 font-mono">
          ${high.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
