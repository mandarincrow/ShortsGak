import { useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";

import { analyzeChatLog } from "./api";
import { LineChart } from "./LineChart";
import type { AnalyzeRequest, AnalyzeResponse } from "./types";

const RECENT_VOD_IDS_KEY = "chatlog_analyzer_recent_vod_ids";
const MAX_RECENT_VOD_IDS = 5;

function formatOffsetForVodUrl(offsetSec: number): string {
  return String(Math.max(0, Math.floor(offsetSec)));
}

function loadRecentVodIds(): string[] {
  if (typeof window === "undefined") {
    return [];
  }

  const stored = window.localStorage.getItem(RECENT_VOD_IDS_KEY);
  if (!stored) {
    return [];
  }

  try {
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((item): item is string => typeof item === "string").slice(0, MAX_RECENT_VOD_IDS);
  } catch {
    return [];
  }
}

export function App() {
  const [vodId, setVodId] = useState("11933431");
  const [recentVodIds, setRecentVodIds] = useState<string[]>(() => loadRecentVodIds());
  const [keywordsText, setKeywordsText] = useState("ㅋㅋㅋㅋ,와");
  const [bucketSize, setBucketSize] = useState(30);
  const [minScore, setMinScore] = useState(1.2);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [focusedPeakBucket, setFocusedPeakBucket] = useState<string | null>(null);
  const [chartWindowSize, setChartWindowSize] = useState<number | null>(null);
  const [chartPanCenter, setChartPanCenter] = useState<number | null>(null);
  const chartSectionRef = useRef<HTMLDivElement | null>(null);

  const keywordList = useMemo(
    () =>
      keywordsText
        .split(",")
        .map((item: string) => item.trim())
        .filter(Boolean),
    [keywordsText]
  );

  const volumeChartPoints = useMemo(
    () =>
      (result?.volume_series ?? []).map((item) => ({
        x: item.bucket_start,
        xLabel: item.bucket_start_offset_label,
        y: item.total_messages,
      })),
    [result]
  );

  const keywordChartPoints = useMemo(() => {
    if (!result) {
      return [];
    }

    const totalByBucket = new Map<string, { total: number; label: string }>();
    for (const point of result.keyword_series) {
      const current = totalByBucket.get(point.bucket_start);
      totalByBucket.set(point.bucket_start, {
        total: (current?.total ?? 0) + point.count,
        label: point.bucket_start_offset_label,
      });
    }

    return Array.from(totalByBucket.entries())
      .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
      .map(([x, value]) => ({ x, xLabel: value.label, y: value.total }));
  }, [result]);

  const highlightMarkers = useMemo(
    () =>
      (result?.highlights ?? []).slice(0, 20).map((item) => ({
        x: item.peak_bucket,
        label: item.peak_offset_label,
      })),
    [result]
  );

  const displayedHighlights = useMemo(() => (result?.highlights ?? []).slice(0, 10), [result]);

  const buildCurrentAnalyzePayload = (): AnalyzeRequest => ({
    source: {
      vod_id: vodId.trim(),
    },
    keywords: keywordList,
    options: {
      bucket_size_seconds: bucketSize,
      keyword_options: {
        mode: "contains",
        case_sensitive: false,
      },
      min_highlight_score: minScore,
      max_highlights: 20,
    },
  });

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    const payload = buildCurrentAnalyzePayload();

    try {
      const analyzed = await analyzeChatLog(payload);
      setResult(analyzed);
      setFocusedPeakBucket(analyzed.highlights[0]?.peak_bucket ?? null);

      const trimmedVodId = vodId.trim();
      if (trimmedVodId) {
        const nextRecentVodIds = [trimmedVodId, ...recentVodIds.filter((item) => item !== trimmedVodId)].slice(
          0,
          MAX_RECENT_VOD_IDS
        );
        setRecentVodIds(nextRecentVodIds);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(RECENT_VOD_IDS_KEY, JSON.stringify(nextRecentVodIds));
        }
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "알 수 없는 오류");
    } finally {
      setLoading(false);
    }
  };

  const handleHighlightFocus = (peakBucket: string) => {
    setFocusedPeakBucket(peakBucket);
    chartSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const focusedHighlightIndex = useMemo(
    () => displayedHighlights.findIndex((item) => item.peak_bucket === focusedPeakBucket),
    [displayedHighlights, focusedPeakBucket]
  );

  const moveHighlightFocus = (direction: "prev" | "next") => {
    if (displayedHighlights.length === 0) {
      return;
    }

    if (focusedHighlightIndex === -1) {
      handleHighlightFocus(displayedHighlights[0].peak_bucket);
      return;
    }

    const nextIndex =
      direction === "prev"
        ? Math.max(0, focusedHighlightIndex - 1)
        : Math.min(displayedHighlights.length - 1, focusedHighlightIndex + 1);

    handleHighlightFocus(displayedHighlights[nextIndex].peak_bucket);
  };

  return (
    <main className="container">
      <div className="page-header">
        <h1>쇼츠각 편집점 분석기</h1>
        <span className="page-header-sub">Chzzk VOD 채팅 기반 편집점 탐색기</span>
      </div>
      <section className="panel">
        <h2>분석 입력</h2>
        <label>
          VOD ID
          <input
            value={vodId}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setVodId(event.target.value)}
            placeholder="예: 11933431"
          />
        </label>

        {recentVodIds.length > 0 ? (
          <div className="recent-vod">
            <p className="recent-vod-title">최근 분석 VOD</p>
            <div className="chip-row">
              {recentVodIds.map((item) => (
                <button key={item} className="chip-button" onClick={() => setVodId(item)}>
                  {item}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <label>
          키워드 (쉼표 구분)
          <input
            value={keywordsText}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setKeywordsText(event.target.value)}
          />
        </label>

        <div className="row">
          <label>
            버킷(초)
            <input
              type="number"
              min={5}
              max={300}
              value={bucketSize}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setBucketSize(Number(event.target.value) || 30)
              }
            />
          </label>

          <label>
            최소 하이라이트 점수
            <input
              type="number"
              step={0.1}
              value={minScore}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setMinScore(Number(event.target.value) || 1.2)
              }
            />
          </label>
        </div>

        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? "분석 중..." : "분석 실행"}
        </button>

        {error ? <p className="error">오류: {error}</p> : null}
      </section>

      <section className="panel">
        <h2>요약</h2>
        {!result ? (
          <p>아직 결과가 없습니다.</p>
        ) : (
          <ul>
            <li>총 메시지: {result.summary.total_messages}</li>
            <li>고유 유저: {result.summary.unique_users}</li>
            <li>VOD 길이(채팅기준): {result.summary.vod_duration_label}</li>
            <li>분당 평균 메시지: {result.summary.avg_messages_per_minute}</li>
            <li>파싱 오류: {result.parse_errors.length}</li>
          </ul>
        )}


      </section>

      <section className="panel">
        <h2>하이라이트 후보 Top 10</h2>
        {!result || displayedHighlights.length === 0 ? (
          <p>조건을 만족하는 하이라이트가 없습니다.</p>
        ) : (
          <>
            <div className="highlight-nav">
              <button
                className="mini-button"
                onClick={() => moveHighlightFocus("prev")}
                disabled={focusedHighlightIndex <= 0}
              >
                이전 하이라이트
              </button>
              <button
                className="mini-button"
                onClick={() => moveHighlightFocus("next")}
                disabled={focusedHighlightIndex === -1 || focusedHighlightIndex >= displayedHighlights.length - 1}
              >
                다음 하이라이트
              </button>
            </div>

            <ol>
              {displayedHighlights.map((item) => (
              <li key={`${item.start}-${item.end}`}>
                  <div className="highlight-row">
                    <button
                      className={`highlight-button ${focusedPeakBucket === item.peak_bucket ? "active" : ""}`}
                      onClick={() => handleHighlightFocus(item.peak_bucket)}
                    >
                      {item.start_offset_label} ~ {item.end_offset_label} | score {item.score} | keyword {item.representative_keyword ?? "-"}
                    </button>
                    {vodId.trim() ? (
                      <a
                        className="vod-link-button"
                        href={`https://chzzk.naver.com/video/${vodId.trim()}?currentTime=${formatOffsetForVodUrl(item.start_offset_sec)}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        VOD 이동
                      </a>
                    ) : null}
                  </div>
              </li>
              ))}
            </ol>
          </>
        )}
      </section>

      <div ref={chartSectionRef}>
        <LineChart
          title="채팅량 추이 (버킷별)"
          points={volumeChartPoints}
          lineColor="#d49fac"
          markers={highlightMarkers}
          focusedX={focusedPeakBucket}
          onClearFocus={() => setFocusedPeakBucket(null)}
          windowSize={chartWindowSize}
          panCenter={chartPanCenter}
          onWindowSizeChange={setChartWindowSize}
          onPanCenterChange={setChartPanCenter}
        />

        <LineChart
          title="키워드 발생량 추이 (합산)"
          points={keywordChartPoints}
          lineColor="#8dad18"
          focusedX={focusedPeakBucket}
          onClearFocus={() => setFocusedPeakBucket(null)}
          windowSize={chartWindowSize}
          panCenter={chartPanCenter}
          onWindowSizeChange={setChartWindowSize}
          onPanCenterChange={setChartPanCenter}
        />
      </div>
    </main>
  );
}
