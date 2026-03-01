/**
 * electron-builder.config.js
 *
 * electron-builder 설정 파일.
 * 코드 서명 인증서 없이 배포하는 빌드용 — CSC_IDENTITY_AUTO_DISCOVERY=false 환경변수로 서명 비활성화.
 */

/** @type {import('electron-builder').Configuration} */
module.exports = {
  appId: "com.mandarincrow.shortsgak",
  productName: "ShortsGak",

  directories: {
    output: "dist/electron",
  },

  files: ["main.js", "utils.js", "package.json", "assets/"],

  extraResources: [
    {
      from: "../dist/backend",
      to: "backend",
      filter: ["**/*"],
    },
  ],

  win: {
    target: [{ target: "dir", arch: ["x64"] }],
    icon: "assets/icon.ico",
  },

  // Windows 코드 서명 완전 비활성화
  // CSC_IDENTITY_AUTO_DISCOVERY=false + WIN_CSC_LINK="" 환경변수로 제어
  // (electron-builder v26: win.sign 속성 미지원 → 환경변수로 우회)
};
