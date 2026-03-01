// no-sign.js — no-op Windows sign script
// electron-builder의 win.sign 에 이 파일을 지정하면
// winCodeSign 다운로드/symlink 생성 단계 자체가 건너뛰어집니다.
// (코드 서명 인증서 없이 배포하는 개발/배포 빌드용)
module.exports = async (_configuration) => {
  // intentionally do nothing — skip Windows code signing
};
