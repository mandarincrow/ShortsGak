## 📌 개요

Electron 데스크톱 앱 배포 파이프라인을 완성하고, 채팅 수집 실시간 진행도 UI를 추가하며, 미니맵 드래그 시 텍스트 선택 버그를 수정합니다.
PyInstaller + electron-builder 빌드 자동화(`build.bat` 5단계)와 릴리즈 ZIP 패키징 스크립트(`package_release.bat`)를 신규 구축했습니다.
아이콘, 메뉴 제거, 외부 링크 처리 등 앱 완성도를 높이는 Electron UX 작업도 포함됩니다.

## 🔖 변경 범위

### Frontend
- [x] `App.tsx` — 채팅 수집 진행도 폴링 (500ms, `fetchProgress` state + interval 정리)
- [x] `api.ts` — `FetchProgress` interface, `getProgress()` 함수 추가
- [x] `LineChart.tsx` — 미니맵 포인터 드래그 중 `document.body.style.userSelect` 토글 (텍스트 선택 버그 수정)
- [x] `styles.css` — `.fetch-progress` 컴포넌트 스타일 + `@keyframes progress-slide` 애니메이션, `.chart-minimap` `user-select: none` + grab 커서

### Backend
- [x] `chatlog_fetcher.py` — `FetchProgress` TypedDict, 모듈 레벨 `_progress` dict, `get_progress()` 함수, `fetch_chatlog_to_file` 내 페이지별 진행도 갱신 (`try/finally`로 `done=True` 보장)
- [x] `main.py` — `GET /api/progress/{vod_id}` 엔드포인트 추가

### Electron / 빌드
- [x] `electron/main.js` — 신규 작성: 메뉴바 제거, 앱 아이콘(`assets/icon.ico`), `AppUserModelId` 설정, 외부 URL → `shell.openExternal()` 처리
- [x] `electron/package.json` — `productName: "ShortsGak"` 추가 (exe 이름 소문자 문제 해결)
- [x] `electron/electron-builder.config.js` — `win.icon: "assets/icon.ico"`, files 배열에 `"assets/"` 추가
- [x] `electron/electron-builder.yml` — 중복 YAML 설정 파일 삭제
- [x] `electron/no-sign.js` — 불필요한 데드코드 삭제
- [x] `scripts/build.bat` — 5단계로 확장 (Electron 빌드 추가), `--config electron-builder.config.js` 플래그 명시
- [x] `scripts/package_release.bat` — 신규: `electron/dist/electron/win-unpacked` → 스테이징 → `tar` ZIP

### 문서
- [x] `README_DEVELOPER.md` — 빌드 출력 경로 수정, `--config` 플래그 명시
- [x] `release/README.txt` — WebView2 항목 제거, 로그 경로 수정, 실행 방법 업데이트
- [x] `ShortsGak.spec.bak` — `.gitignore` 추가 및 git rm --cached 처리

## 🖼️ 스크린샷 / 데모

<!-- 채팅 수집 진행도 UI, 아이콘 적용 화면 첨부 예정 -->

## ✅ 테스트

- [x] `scripts/build.bat` 전체 빌드 통과 (Frontend → PyInstaller → electron-builder)
- [x] `scripts/package_release.bat` ZIP 생성 확인 (`tar -a` 방식)
- [x] 릴리즈 ZIP 더블클릭 실행 확인
- [x] 채팅 수집 중 진행도 폴링 동작 확인
- [x] 외부 링크 → 시스템 기본 브라우저 열림 확인
- [x] 미니맵 드래그 시 텍스트 선택 없음 확인

## ⚠️ 브레이킹 체인지

없음

## 📦 배포 메모

- `electron-builder` 실행 시 `--config electron-builder.config.js` 플래그 필수 (CLI에서 직접 실행할 경우)
- `assets/icon.ico` 파일이 `electron/assets/` 에 존재해야 빌드 성공
- `package_release.bat` 실행 전 `build.bat` 완료 필요 (win-unpacked 디렉터리 존재해야 함)

## 🚀 릴리즈 체크리스트

- [x] `VERSION` 파일 — `v1.0.0-beta3.rc1` 확인
- [x] `release/README.txt` 최신 상태
- [ ] `electron/package.json` `version` 동기화 (현재 `1.0.0`, VERSION과 맞추기)
- [ ] PR 머지 후 GitHub Release 태그 생성 (`v1.0.0-beta3`)
