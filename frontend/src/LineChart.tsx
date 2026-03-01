import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
  // lifted state — shared across charts
  windowSize: number | null;
  panCenter: number | null;
  onWindowSizeChange: (v: number | null) => void;
  onPanCenterChange: (v: number | null) => void;
};

// R2 fix: single source-of-truth for chart padding
const CHART_PADDING = 28;
const SVG_WIDTH = 860;
const ZOOM_MIN_WINDOW = 10;
const ZOOM_STEPS = [10, 20, 40, 80, 160, 320, 640, 1280, Infinity];
const MINIMAP_H = 40;
const MINIMAP_PAD = 4;

// R6 fix: use reduce instead of Math.max(...spread) to avoid stack overflow on large arrays
function safeMax(arr: number[], fallback: number): number {
  return arr.length === 0 ? fallback : arr.reduce((a, b) => (b > a ? b : a), arr[0]);
}
function safeMin(arr: number[], fallback: number): number {
  return arr.length === 0 ? fallback : arr.reduce((a, b) => (b < a ? b : a), arr[0]);
}

function buildPath(points: DataPoint[], width: number, height: number, padding: number): string {
  if (points.length === 0) return "";
  const ys = points.map((p) => p.y);
  const maxY = Math.max(safeMax(ys, 1), 1);
  const minY = Math.min(safeMin(ys, 0), 0);
  const xSpan = Math.max(points.length - 1, 1);
  const ySpan = Math.max(maxY - minY, 1);
  return points
    .map((p, i) => {
      const x = padding + (i / xSpan) * (width - padding * 2);
      const y = height - padding - ((p.y - minY) / ySpan) * (height - padding * 2);
      return `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

export function LineChart({
  title,
  points,
  lineColor = "#2563eb",
  markers = [],
  height = 220,
  focusedX = null,
  onClearFocus = null,
  windowSize,
  panCenter,
  onWindowSizeChange,
  onPanCenterChange,
}: LineChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const svgRef = useRef<SVGSVGElement>(null);
  const minimapRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<{ startX: number; startCenter: number } | null>(null);

  // ── View calculation ──────────────────────────────────────────────────────

  // R4 fix: memoize index map — O(n) Map build should not repeat every render
  const fullIndexMap = useMemo(
    () => new Map(points.map((p, i) => [p.x, i])),
    [points]
  );
  const focusedSourceIndex = focusedX != null ? fullIndexMap.get(focusedX) : undefined;

  const clampedWindow = Math.min(windowSize ?? points.length, points.length);
  const effectiveCenter = panCenter ?? focusedSourceIndex ?? Math.floor(points.length / 2);
  const viewStart = Math.max(
    0,
    Math.min(points.length - clampedWindow, effectiveCenter - Math.floor(clampedWindow / 2))
  );
  const viewEnd = Math.min(points.length - 1, viewStart + clampedWindow - 1);
  const isFullView = clampedWindow >= points.length;

  // R1 fix: declare displayPoints early so all handlers can reference it without forward ref
  const displayPoints = points.slice(viewStart, viewEnd + 1);
  const displayPointXSet = new Set(displayPoints.map((p) => p.x));
  const displayMarkers = markers.filter((m) => displayPointXSet.has(m.x));

  // Sync panCenter + windowSize (lifted) when focused highlight changes
  useEffect(() => {
    if (focusedSourceIndex !== undefined) {
      onPanCenterChange(focusedSourceIndex);
      onWindowSizeChange(40);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusedSourceIndex]);

  // ── Panning ───────────────────────────────────────────────────────────────

  const panTo = useCallback(
    (center: number) => {
      onPanCenterChange(Math.max(0, Math.min(points.length - 1, center)));
    },
    [points.length, onPanCenterChange]
  );

  // R5 fix: typed ref, initialized once; kept current via assignment in render body
  // (assignment in render is safe here because panToRef is only read in event callbacks)
  const panToRef = useRef<(center: number) => void>(panTo);
  panToRef.current = panTo;

  const handlePanStart = () => panTo(Math.floor(clampedWindow / 2));
  const handlePanLeft  = () => panTo(effectiveCenter - Math.floor(clampedWindow / 2));
  const handlePanRight = () => panTo(effectiveCenter + Math.floor(clampedWindow / 2));
  const handlePanEnd   = () => panTo(points.length - 1 - Math.floor(clampedWindow / 2));

  // ── Zoom ──────────────────────────────────────────────────────────────────

  const handleZoomIn = () => {
    const cur = windowSize ?? points.length;
    const filtered = ZOOM_STEPS.filter((s) => s < cur);
    onWindowSizeChange(Math.max(ZOOM_MIN_WINDOW, filtered.length > 0 ? filtered[filtered.length - 1] : ZOOM_MIN_WINDOW));
  };

  const handleZoomOut = () => {
    const cur = windowSize ?? points.length;
    const next = ZOOM_STEPS.find((s) => s > cur) ?? Infinity;
    onWindowSizeChange(next >= points.length ? null : next);
  };

  const handleReset = () => {
    onWindowSizeChange(null);
    onPanCenterChange(null);
    onClearFocus?.();
  };

  // ── SVG click to re-center ────────────────────────────────────────────────
  // R3 fix: removed isDraggingRef check — minimap and main SVG are separate elements,
  //         pointer events can't overlap, so the guard was dead code.

  const handleSvgClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current || displayPoints.length <= 1) return;
    const rect = svgRef.current.getBoundingClientRect();
    const chartLeft  = (CHART_PADDING / SVG_WIDTH) * rect.width;
    const chartWidth = ((SVG_WIDTH - CHART_PADDING * 2) / SVG_WIDTH) * rect.width;
    const ratio = (e.clientX - rect.left - chartLeft) / chartWidth;
    if (ratio < 0 || ratio > 1) return;
    const clickedDisplayIdx = Math.round(ratio * (displayPoints.length - 1));
    panTo(viewStart + clickedDisplayIdx);
  };

  // ── Minimap pointer events ────────────────────────────────────────────────

  const handleMinimapPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!minimapRef.current) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    document.body.style.userSelect = 'none';
    const rect = minimapRef.current.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const newCenter = Math.round(ratio * (points.length - 1));
    panToRef.current(newCenter);
    dragRef.current = { startX: e.clientX, startCenter: newCenter };
  };

  const handleMinimapPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!dragRef.current || !minimapRef.current) return;
    const rect = minimapRef.current.getBoundingClientRect();
    const dx = e.clientX - dragRef.current.startX;
    const delta = Math.round((dx / rect.width) * points.length);
    panToRef.current(dragRef.current.startCenter + delta);
  };

  const handleMinimapPointerUp = () => {
    dragRef.current = null;
    document.body.style.userSelect = '';
  };

  // ── Derived render values ─────────────────────────────────────────────────

  const ys = displayPoints.map((p) => p.y);
  const minY = Math.min(safeMin(ys, 0), 0);
  const maxY = Math.max(safeMax(ys, 1), 1);
  const ySpan = Math.max(maxY - minY, 1);
  const path = buildPath(displayPoints, SVG_WIDTH, height, CHART_PADDING);
  const xIndexMap = new Map(displayPoints.map((p, i) => [p.x, i]));
  const focusedIndex = focusedX != null ? xIndexMap.get(focusedX) : undefined;

  const tickCount = 6;
  const tickStep = Math.max(1, Math.floor((displayPoints.length - 1) / tickCount));
  const tickIndices = Array.from(
    new Set([0, ...Array.from({ length: tickCount }, (_, i) => i * tickStep), displayPoints.length - 1])
  )
    .filter((i) => i >= 0 && i < displayPoints.length)
    .sort((a, b) => a - b);

  const getX = (idx: number) =>
    CHART_PADDING + (idx / Math.max(displayPoints.length - 1, 1)) * (SVG_WIDTH - CHART_PADDING * 2);
  const getY = (idx: number) => {
    const p = displayPoints[idx];
    return height - CHART_PADDING - ((p.y - minY) / ySpan) * (height - CHART_PADDING * 2);
  };

  // R4 fix: memoize minimap path — re-computed only when full points array changes
  const minimapPath = useMemo(
    () => buildPath(points, SVG_WIDTH, MINIMAP_H, MINIMAP_PAD),
    [points]
  );
  const vpLeft  = CHART_PADDING + (viewStart / Math.max(points.length - 1, 1)) * (SVG_WIDTH - CHART_PADDING * 2);
  const vpRight = CHART_PADDING + (viewEnd   / Math.max(points.length - 1, 1)) * (SVG_WIDTH - CHART_PADDING * 2);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <section className="panel">
      <h2>{title}</h2>
      {displayPoints.length === 0 ? (
        <p>표시할 데이터가 없습니다.</p>
      ) : (
        <div className="chart-wrapper">

          {/* Control bar */}
          <div className="chart-meta">
            <span className="chart-range-label">
              {isFullView
                ? `전체 (${points.length}개 버킷)`
                : `${displayPoints[0]?.xLabel} ~ ${displayPoints[displayPoints.length - 1]?.xLabel} (${displayPoints.length} / ${points.length})`}
            </span>
            <div className="chart-controls">
              {!isFullView && (
                <>
                  <button className="mini-button" onClick={handlePanStart} disabled={viewStart === 0} title="처음">
                    &#9664;&#9664;
                  </button>
                  <button className="mini-button" onClick={handlePanLeft} disabled={viewStart === 0} title="이전">
                    &#9664;
                  </button>
                </>
              )}
              <button className="mini-button" onClick={handleZoomIn} disabled={clampedWindow <= ZOOM_MIN_WINDOW} title="확대">
                +
              </button>
              <button className="mini-button" onClick={handleZoomOut} disabled={isFullView} title="축소">
                &#8722;
              </button>
              {!isFullView && (
                <>
                  <button className="mini-button" onClick={handlePanRight} disabled={viewEnd >= points.length - 1} title="다음">
                    &#9654;
                  </button>
                  <button className="mini-button" onClick={handlePanEnd} disabled={viewEnd >= points.length - 1} title="끝">
                    &#9654;&#9654;
                  </button>
                  <button className="mini-button chart-reset-btn" onClick={handleReset} title="전체 보기">
                    전체
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Main chart — click to re-center view */}
          <svg
            ref={svgRef}
            viewBox={`0 0 ${SVG_WIDTH} ${height}`}
            className="chart-svg"
            role="img"
            aria-label={title}
            onClick={handleSvgClick}
            style={{ cursor: isFullView ? "default" : "crosshair" }}
          >
            <line x1={CHART_PADDING} y1={height - CHART_PADDING} x2={SVG_WIDTH - CHART_PADDING} y2={height - CHART_PADDING} stroke="#cbd5e1" strokeWidth="1" />
            <line x1={CHART_PADDING} y1={CHART_PADDING} x2={CHART_PADDING} y2={height - CHART_PADDING} stroke="#cbd5e1" strokeWidth="1" />

            <text x={8} y={CHART_PADDING + 4} fontSize="11" fill="#5a4248">{maxY}</text>
            <text x={8} y={height - CHART_PADDING + 4} fontSize="11" fill="#5a4248">0</text>

            <path d={path} fill="none" stroke={lineColor} strokeWidth="2" />

            {focusedIndex !== undefined && (
              <line
                x1={getX(focusedIndex)} y1={CHART_PADDING}
                x2={getX(focusedIndex)} y2={height - CHART_PADDING}
                stroke="#935260" strokeWidth="2"
              />
            )}

            {tickIndices.map((idx) => {
              const p = displayPoints[idx];
              const x = getX(idx);
              return (
                <g key={`tick-${p.x}-${idx}`}>
                  <line x1={x} y1={height - CHART_PADDING} x2={x} y2={height - CHART_PADDING + 5} stroke="#94a3b8" strokeWidth="1" />
                  <text x={x} y={height - CHART_PADDING + 16} fontSize="10" fill="#5a4248" textAnchor="middle">
                    {p.xLabel}
                  </text>
                </g>
              );
            })}

            {displayMarkers.map((marker) => {
              const idx = xIndexMap.get(marker.x);
              if (idx === undefined) return null;
              const x = getX(idx);
              return (
                <g key={`${marker.x}-${marker.label}`}>
                  <line x1={x} y1={CHART_PADDING} x2={x} y2={height - CHART_PADDING} stroke="#ef4444" strokeDasharray="4 3" strokeWidth="1" />
                  <text x={x} y={CHART_PADDING - 6} fontSize="10" fill="#ef4444" textAnchor="middle">
                    {marker.label}
                  </text>
                </g>
              );
            })}

            {displayPoints.map((p, idx) => (
              <circle
                key={`point-${p.x}-${idx}`}
                cx={getX(idx)} cy={getY(idx)} r="6"
                fill={idx === focusedIndex ? "#935260" : lineColor}
                fillOpacity="0"
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
            ))}

            {hoveredIndex !== null && (
              <g>
                <rect
                  x={Math.min(getX(hoveredIndex) + 8, SVG_WIDTH - 180)}
                  y={Math.max(getY(hoveredIndex) - 45, 6)}
                  width="170" height="36" rx="6"
                  fill="#0f172a" fillOpacity="0.9"
                />
                <text
                  x={Math.min(getX(hoveredIndex) + 16, SVG_WIDTH - 172)}
                  y={Math.max(getY(hoveredIndex) - 28, 20)}
                  fontSize="10" fill="#ffffff"
                >
                  {displayPoints[hoveredIndex].xLabel}
                </text>
                <text
                  x={Math.min(getX(hoveredIndex) + 16, SVG_WIDTH - 172)}
                  y={Math.max(getY(hoveredIndex) - 14, 34)}
                  fontSize="10" fill="#ffffff"
                >
                  {displayPoints[hoveredIndex].y}
                </text>
              </g>
            )}
          </svg>

          {/* Minimap — shown only when zoomed in; click/drag to pan */}
          {!isFullView && (
            <svg
              ref={minimapRef}
              viewBox={`0 0 ${SVG_WIDTH} ${MINIMAP_H}`}
              className="chart-minimap"
              onPointerDown={handleMinimapPointerDown}
              onPointerMove={handleMinimapPointerMove}
              onPointerUp={handleMinimapPointerUp}
              onPointerCancel={handleMinimapPointerUp}
              style={{ cursor: "ew-resize" }}
            >
              <path d={minimapPath} fill="none" stroke={lineColor} strokeWidth="1" opacity="0.3" />
              <rect
                x={vpLeft} y={MINIMAP_PAD}
                width={Math.max(vpRight - vpLeft, 2)}
                height={MINIMAP_H - MINIMAP_PAD * 2}
                fill={lineColor} fillOpacity="0.15"
                stroke={lineColor} strokeWidth="1" strokeOpacity="0.6"
                rx="2"
              />
              <line x1={vpLeft}  y1={MINIMAP_PAD} x2={vpLeft}  y2={MINIMAP_H - MINIMAP_PAD} stroke={lineColor} strokeWidth="1.5" />
              <line x1={vpRight} y1={MINIMAP_PAD} x2={vpRight} y2={MINIMAP_H - MINIMAP_PAD} stroke={lineColor} strokeWidth="1.5" />
            </svg>
          )}

        </div>
      )}
    </section>
  );
}
