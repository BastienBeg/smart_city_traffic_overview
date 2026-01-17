import React from "react";

interface GaugeProps {
  value: number; // 0 to 100
  label: string;
  unit: string;
  max?: number; // Default 100
  status?: "healthy" | "warning" | "critical";
  size?: number;
}

export const Gauge: React.FC<GaugeProps> = ({
  value,
  label,
  unit,
  max = 100,
  status = "healthy",
  size = 120,
}) => {
  const radius = size * 0.4;
  const strokeWidth = size * 0.1;
  const circumference = 2 * Math.PI * radius;
  
  // Normalize value to 0-100 relative to max
  const normalizedValue = Math.min(Math.max(value, 0), max);
  const percentage = (normalizedValue / max) * 100;
  
  // Half-circle gauge (180 degrees)
  // We want to fill from left to right.
  // Full circle context:
  // stroke-dasharray = circumference
  // offset = circumference - (percentage * circumference)
  // But for a semi-circle gauge, we often use a full circle with 50% cutoff or a specific dasharray.
  
  // Let's do a simple 270 degree gauge (standard speedometer style)
  // Or a nice ring. Let's do a ring for simplicity and elegance.
  const offset = circumference - (percentage / 100) * circumference;

  let colorClass = "text-cyan-500 shadow-cyan-500/50";
  if (status === "warning") colorClass = "text-yellow-500 shadow-yellow-500/50";
  if (status === "critical") colorClass = "text-red-500 shadow-red-500/50";

  // Tailwind neon classes
  const strokeColor = {
    healthy: "#06b6d4", // cyan-500
    warning: "#eab308", // yellow-500
    critical: "#ef4444", // red-500
  }[status];

  return (
    <div className="flex flex-col items-center justify-center pointer-events-none select-none">
      <div className="relative flex items-center justify-center">
        {/* SVG Container */}
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="transform -rotate-90"
        >
          {/* Background Track */}
          <circle
            className="text-gray-800"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="transparent"
            r={radius}
            cx={size / 2}
            cy={size / 2}
          />
          {/* Progress Indicator */}
          <circle
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            fill="transparent"
            r={radius}
            cx={size / 2}
            cy={size / 2}
            className={`transition-all duration-500 ease-out drop-shadow-[0_0_8px_${strokeColor}]`}
          />
        </svg>
        
        {/* Value Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${colorClass.split(' ')[0]} drop-shadow-md`}>
            {value}
          </span>
          <span className="text-xs text-gray-400 font-mono">{unit}</span>
        </div>
      </div>
      
      {/* Label */}
      <div className="mt-2 text-sm font-semibold text-gray-300 tracking-wider uppercase">
        {label}
      </div>
    </div>
  );
};
