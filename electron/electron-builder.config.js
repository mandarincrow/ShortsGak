/**
 * electron-builder.config.js
 *
 * JS 설정 파일로 YAML 대신 사용 (electron-builder.yml보다 우선 로드됨).
 * win.sign 에 no-op 함수를 직접 지정 → winCodeSign 다운로드/symlink 오류 방지.
 * (코드 서명 인증서 없이 배포하는 개발/배포 빌드용)
 */

/** @type {import('electron-builder').Configuration} */
module.exports = {
  appId: "com.mandarincrow.shortsgak",
  productName: "ShortsGak",

  directories: {
    output: "dist/electron",
  },

  files: ["main.js", "utils.js", "package.json"],

  extraResources: [
    {
      from: "../dist/backend",
      to: "backend",
      filter: ["**/*"],
    },
  ],

  win: {
    target: [{ target: "dir", arch: ["x64"] }],
  },

  // Windows 코드 서명 완전 비활성화
  // CSC_IDENTITY_AUTO_DISCOVERY=false + WIN_CSC_LINK="" 환경변수로 제어
  // (electron-builder v26: win.sign 속성 미지원 → 환경변수로 우회)
};
