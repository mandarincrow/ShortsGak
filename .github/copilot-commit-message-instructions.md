Generate a commit message following these rules:

!!! IMPORTANT RULE !!!
- commit message should be written in Korean
- What/Why and How sections shold not over 72 characters per line

Format:
```txt
[<type>](<scope>): <short summary>

:What/Why:
- Describe what was changed and why it was changed. This section is mandatory and list of the changes
- Each change should not exceed 72 characters and should be listed in a bullet point format.

:How:
- Describe how the change was implemented. This section is optional but can be helpful for reviewers.
```

Example:
```txt
[fea](parser): 채팅 로그 파싱 기능 추가

:What/Why:
- 채팅 로그 파일을 파싱하여 분석할 수 있도록 analyzer 모듈에 새로운 기능 추가
- 기존에는 채팅 로그 파일을 직접 분석해야 했지만, 이제는 파싱 기능을 통해 더 쉽게 분석할 수 있음

:How:
- parser 모듈에 parse_chatlog 함수를 추가하여 채팅 로그 파일을 파싱하도록 구현
```

Types:
- fea: new feature
- fix: bug fix
- docs: documentation changes only
- style: formatting, missing semicolons, etc (no logic change)
- refactor: code change that is not a fix or feature or performance improvement
- perf: performance improvement
- test: adding or updating tests
- chore: build process, dependency updates, config changes
- ci: CI/CD configuration changes
- revert: reverting a previous commit

Scope (optional): the part of the codebase affected, e.g. backend, frontend, parser, analyzer, ui

Rules:
- Summary line must be 50 characters or less
- Use the imperative mood ("add feature" not "added feature")
- Do not end the summary line with a period
- If the change is complex, add a blank line followed by a body explaining what and why (wrap at 72 chars)
- If the change closes a GitHub issue, add "Closes #<number>" in the footer

Examples:
  feat(frontend): add chat volume line chart
  fix(parser): handle empty chatlog file gracefully
  refactor(backend): split analyzer into smaller modules
  chore: update Python dependencies