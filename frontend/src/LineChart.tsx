import { useState } from "react";

type DataPoint = {
  x: string;
  xLabel: string;
  y: number;
};

type Marker = {
  x: string;
  label: string;
};

type LineChartProps = {
  title: string;
  points: DataPoint[];
  lineColor?: string;
  markers?: Marker[];
  height?: number;
  focusedX?: string | null;
  onClearFocus?: (() => void) | null;
};

function buildPath(points: DataPoint[], width: number, height: number, padding: number): string {
  if (points.length === 0) {
    return "";
  }

  const maxY = Math.max(...points.map((point) => point.y), 1);
  const minY = Math.min(...points.map((point) => point.y), 0);
  const xSpan = Math.max(points.length - 1, 1);
  const ySpan = Math.max(maxY - minY, 1);

  return points
    .map((point, index) => {
      const x = padding + (index / xSpan) * (width - padding * 2);
      const y = height - padding - ((point.y - minY) / ySpan) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

const ZOOM_MIN_WINDOW = 10;
const ZOOM_STEPS = [10, 20, 40, 80, 160, 320, 640, 1280, Infinity];

export function LineChart({
  title,
  points,
  lineColor = "#2563eb",
  markers = [],
  height = 220,
  focusedX = null,
  onClearFocus = null,
}: LineChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  // null = 전체 보기, number = 표시할 포인트 수
  const [windowSize, setWindowSize] = useState<number | null>(null);

  const fullIndexMap = new Map(points.map((point, index) => [point.x, index]));
  const focusedSourceIndex = focusedX ? fullIndexMap.get(focusedX) : undefined;

  // 유효 윈도우: 명시적 windowSize 우선, 없으면 전체
  const effectiveWindow = windowSize !== null ? windowSize : points.length;
  const clampedWindow = Math.min(effectiveWindow, points.length);
  // 뷰 중심: 포커스된 포인트 > 전체 중간
  const centerIndex = focusedSourceIndex ?? Math.floor(points.length / 2);
  const viewStart = Math.max(0, Math.min(points.length - clampedWindow, centerIndex - Math.floor(clampedWindow / 2)));
  const viewEnd = Math.min(points.length - 1, viewStart + clampedWindow - 1);

  const isFullView = windowSize === null || clampedWindow >= points.length;

  const handleZoomIn = () => {
    const current = windowSize !== null ? windowSize : points.length;
    const filtered = ZOOM_STEPS.filter((s) => s < current);
    const next = filtered.length > 0 ? filtered[filtered.length - 1] : ZOOM_MIN_WINDOW;
    setWindowSize(Math.max(ZOOM_MIN_WINDOW, next));
  };

  const handleZoomOut = () => {
    const current = windowSize !== null ? windowSize : points.length;
    const next = ZOOM_STEPS.find((s) => s > current) ?? Infinity;
    if (next >= points.length) {
      setWindowSize(null);
    } else {
      setWindowSize(next);
    }
  };

  const handleReset = () => {
    setWindowSize(null);
    onClearFocus?.();
  };

  const displayPoints = points.slice(viewStart, viewEnd + 1);
  const displayPointXSet = new Set(displayPoints.map((point) => point.x));
  const displayMarkers = markers.filter((marker) => displayPointXSet.has(marker.x));

  const width = 860;
  const padding = 28;
  const minY = Math.min(...displayPoints.map((point) => point.y), 0);
  const maxY = Math.max(...displayPoints.map((point) => point.y), 1);
  const ySpan = Math.max(maxY - minY, 1);
  const path = buildPath(displayPoints, width, height, padding);
  const xIndexMap = new Map(displayPoints.map((point, index) => [point.x, index]));
  const focusedIndex = focusedX ? xIndexMap.get(focusedX) : undefined;
  const tickCount = 6;
  const tickStep = Math.max(1, Math.floor((displayPoints.length - 1) / tickCount));
  const tickIndices = Array.from(
    new Set([0, ...Array.from({ length: tickCount }, (_, idx) => idx * tickStep), displayPoints.length - 1])
  )
    .filter((index) => index >= 0 && index < displayPoints.length)
    .sort((left, right) => left - right);

  const getX = (idx: number) =>
    padding + (idx / Math.max(displayPoints.length - 1, 1)) * (width - padding * 2);
  const getY = (idx: number) => {
    const point = displayPoints[idx];
    return height - padding - ((point.y - minY) / ySpan) * (height - padding * 2);
  };

  return (
    <section className="panel">
      <h2>{title}</h2>
      {displayPoints.length === 0 ? (
        <p>표시할 데이터가 없습니다.</p>
      ) : (
        <div className="chart-wrapper">
          <div className="chart-meta">
            <span>
              {isFullView
                ? `전체 (${points.length}개 버킷)`
                : `${displayPoints[0]?.xLabel} ~ ${displayPoints[displayPoints.length - 1]?.xLabel} (${displayPoints.length}/${points.length})`}
            </span>
            <div className="chart-controls">
              <button
                className="mini-button"
                onClick={handleZoomIn}
                disabled={clampedWindow <= ZOOM_MIN_WINDOW}
                title="확대"
              >
                + 확대
              </button>
              <button
                className="mini-button"
                onClick={handleZoomOut}
                disabled={isFullView}
                title="축소"
              >
                − 축소
              </button>
              {(!isFullView || focusedX) ? (
                <button className="mini-button" onClick={handleReset}>
                  전체 보기
                </button>
              ) : null}
            </div>
          </div>
          <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg" role="img" aria-label={title}>
            <line
              x1={padding}
              y1={height - padding}
              x2={width - padding}
              y2={height - padding}
              stroke="#cbd5e1"
              strokeWidth="1"
            />
            <line
              x1={padding}
              y1={padding}
              x2={padding}
              y2={height - padding}
              stroke="#cbd5e1"
              strokeWidth="1"
            />

            <text x={8} y={padding + 4} fontSize="11" fill="#64748b">
              {maxY}
            </text>
            <text x={8} y={height - padding + 4} fontSize="11" fill="#64748b">
              0
            </text>

            <path d={path} fill="none" stroke={lineColor} strokeWidth="2" />

            {focusedIndex !== undefined ? (
              <line
                x1={getX(focusedIndex)}
                y1={padding}
                x2={getX(focusedIndex)}
                y2={height - padding}
                stroke="#f59e0b"
                strokeWidth="2"
              />
            ) : null}

            {tickIndices.map((idx) => {
              const point = displayPoints[idx];
              const x = getX(idx);
              return (
                <g key={`tick-${point.x}-${idx}`}>
                  <line
                    x1={x}
                    y1={height - padding}
                    x2={x}
                    y2={height - padding + 5}
                    stroke="#94a3b8"
                    strokeWidth="1"
                  />
                  <text x={x} y={height - padding + 16} fontSize="10" fill="#64748b" textAnchor="middle">
                    {point.xLabel}
                  </text>
                </g>
              );
            })}

            {displayMarkers.map((marker) => {
              const idx = xIndexMap.get(marker.x);
              if (idx === undefined) {
                return null;
              }
              const x = getX(idx);
              return (
                <g key={`${marker.x}-${marker.label}`}>
                  <line
                    x1={x}
                    y1={padding}
                    x2={x}
                    y2={height - padding}
                    stroke="#ef4444"
                    strokeDasharray="4 3"
                    strokeWidth="1"
                  />
                  <text x={x} y={padding - 6} fontSize="10" fill="#ef4444" textAnchor="middle">
                    {marker.label}
                  </text>
                </g>
              );
            })}

            {displayPoints.map((point, idx) => {
              const x = getX(idx);
              const y = getY(idx);
              return (
                <circle
                  key={`point-${point.x}-${idx}`}
                  cx={x}
                  cy={y}
                  r="4"
                  fill={idx === focusedIndex ? "#f59e0b" : lineColor}
                  fillOpacity="0"
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onMouseLeave={() => setHoveredIndex(null)}
                />
              );
            })}

            {hoveredIndex !== null ? (
              <g>
                <rect
                  x={Math.min(getX(hoveredIndex) + 8, width - 180)}
                  y={Math.max(getY(hoveredIndex) - 45, 6)}
                  width="170"
                  height="36"
                  rx="6"
                  fill="#0f172a"
                  fillOpacity="0.9"
                />
                <text
                  x={Math.min(getX(hoveredIndex) + 16, width - 172)}
                  y={Math.max(getY(hoveredIndex) - 28, 20)}
                  fontSize="10"
                  fill="#ffffff"
                >
                  {displayPoints[hoveredIndex].xLabel}
                </text>
                <text
                  x={Math.min(getX(hoveredIndex) + 16, width - 172)}
                  y={Math.max(getY(hoveredIndex) - 14, 34)}
                  fontSize="10"
                  fill="#ffffff"
                >
                  값: {displayPoints[hoveredIndex].y}
                </text>
              </g>
            ) : null}
          </svg>
        </div>
      )}
    </section>
  );
}
