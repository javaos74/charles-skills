# charles-skills

마케팅 운영 및 보안 검증 업무를 위한 재사용 가능한 Claude Code 및 Codex 스킬 모음입니다. 각 스킬은 `skills/<skill-name>/SKILL.md`를 진입점으로 가지며 독립적으로 설치하고 테스트할 수 있습니다.

## Skills

| Skill | Description |
| --- | --- |
| [`converting-marketing-event-data`](skills/converting-marketing-event-data/SKILL.md) | 행사 참석자 Excel을 Marketo Robot Import Lead Template 형식으로 변환합니다. |
| [`cve-validator`](skills/cve-validator/SKILL.md) | CVE 스캐너 결과(.xlsx)를 최신 NVD 레코드와 대조하고 Windows DLL/EXE 바이너리를 정적 분석하여 정탐/오탐/검토 필요를 판정합니다. |

## 설치

저장소를 복제한 뒤 전체 스킬 또는 원하는 스킬 하나만 설치합니다.

```bash
git clone https://github.com/javaos74/charles-skills.git
cd charles-skills

# 모든 스킬을 Claude(~/.claude/skills)와 Codex(~/.codex/skills)에 설치
./scripts/install.sh

# 특정 플랫폼에만 설치
./scripts/install.sh --claude-only
./scripts/install.sh --codex-only

# 특정 스킬만 설치 (기본은 Claude + Codex 양쪽)
./scripts/install-skill.sh cve-validator
./scripts/install-skill.sh converting-marketing-event-data --claude-only
```

설치 스크립트는 스킬 폴더를 복사하지 않고 심볼릭 링크를 만듭니다. 저장소를 `git pull`하면 설치된 스킬에도 변경 사항이 바로 반영됩니다. 기존의 일반 디렉터리나 파일은 자동으로 덮어쓰지 않습니다. 설치 경로는 환경 변수 `CLAUDE_SKILLS_DIR` / `CODEX_SKILLS_DIR`로 재정의할 수 있습니다.

## 저장소 구조

```text
charles-skills/
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── requirements.txt
│       ├── reference/
│       ├── examples/
│       └── tests/
├── scripts/
│   ├── install.sh
│   ├── install-skill.sh
│   └── validate-repo.py
├── tests/
├── .github/workflows/test.yml
├── CONTRIBUTING.md
└── LICENSE
```

## 개발 및 검증

프로젝트의 Python 가상환경을 활성화한 뒤 개발 의존성과 각 스킬의 의존성을 설치합니다.

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r skills/converting-marketing-event-data/requirements.txt
python scripts/validate-repo.py
python -m pytest
```

실제 참석자 명단에는 개인정보가 포함되므로 커밋하지 마십시오. Excel 샘플은 익명화된 `skills/*/examples/` 파일만 허용합니다.

## 새 스킬 추가

[`CONTRIBUTING.md`](CONTRIBUTING.md)의 폴더 규칙과 검증 절차를 따르십시오.

## License

MIT License. 자세한 내용은 [`LICENSE`](LICENSE)를 참조하십시오.
