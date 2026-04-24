#!/usr/bin/env node

/**
 * 🔧 멀티 언어 프로젝트 하네스 엔지니어링 최적화 에이전트
 * 
 * 기능:
 * - 멀티 언어 프로젝트 구조 분석
 * - 빌드 하네스 효율화
 * - 의존성 최적화
 * - CI/CD 파이프라인 개선
 * - 테스트 자동화 강화
 * 
 * 사용법:
 * node harness-optimizer.js --project ./my-project --analyze
 * node harness-optimizer.js --project ./my-project --optimize --commit
 */

const Anthropic = require("@anthropic-ai/sdk");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const client = new Anthropic();

class HarnessOptimizer {
  constructor(projectPath) {
    this.projectPath = projectPath;
    this.projectStructure = {};
    this.analysisResult = null;
    this.optimizations = [];
    this.metrics = {
      languages: [],
      buildSystems: [],
      testFrameworks: [],
      ciSystems: [],
    };
  }

  // ========== 프로젝트 구조 분석 ==========
  analyzeProjectStructure() {
    console.log("\n📊 멀티 언어 프로젝트 구조 분석 중...\n");

    const structure = {
      languages: this.detectLanguages(),
      buildSystems: this.detectBuildSystems(),
      testFrameworks: this.detectTestFrameworks(),
      ciSystems: this.detectCISystems(),
      dependencyManagers: this.detectDependencyManagers(),
      projectLayout: this.analyzeDirectoryLayout(),
    };

    this.projectStructure = structure;
    this.displayStructure();
    return structure;
  }

  // 사용된 언어 감지
  detectLanguages() {
    const languagePatterns = {
      JavaScript: [".js", ".jsx", ".mjs"],
      TypeScript: [".ts", ".tsx"],
      Python: [".py"],
      Java: [".java"],
      Go: [".go"],
      Rust: [".rs"],
      CSharp: [".cs"],
      Ruby: [".rb"],
      PHP: [".php"],
      C: [".c", ".h"],
      "C++": [".cpp", ".cc", ".cxx", ".h"],
    };

    const extensions = {};
    const detected = [];

    const walk = (dir, depth = 0) => {
      if (depth > 3) return;
      if (
        [
          "node_modules",
          ".git",
          "build",
          "dist",
          "target",
          "vendor",
          "__pycache__",
        ].includes(path.basename(dir))
      )
        return;

      try {
        const items = fs.readdirSync(dir);
        for (const item of items) {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);

          if (stat.isFile()) {
            const ext = path.extname(item);
            extensions[ext] = (extensions[ext] || 0) + 1;
          } else if (stat.isDirectory()) {
            walk(fullPath, depth + 1);
          }
        }
      } catch {}
    };

    walk(this.projectPath);

    // 언어 매핑
    Object.entries(languagePatterns).forEach(([lang, exts]) => {
      if (exts.some((ext) => extensions[ext] > 0)) {
        detected.push({
          name: lang,
          fileCount: exts.reduce((sum, ext) => sum + (extensions[ext] || 0), 0),
        });
      }
    });

    return detected.sort((a, b) => b.fileCount - a.fileCount);
  }

  // 빌드 시스템 감지
  detectBuildSystems() {
    const buildFiles = {
      "npm": ["package.json"],
      "Maven": ["pom.xml"],
      "Gradle": ["build.gradle", "build.gradle.kts"],
      "Cargo": ["Cargo.toml"],
      "Poetry": ["pyproject.toml"],
      "Make": ["Makefile"],
      "Cmake": ["CMakeLists.txt"],
      "Bazel": ["BUILD", "WORKSPACE"],
      "Meson": ["meson.build"],
      "Go Modules": ["go.mod"],
      "dotnet": [".csproj", ".sln"],
      "Bundler": ["Gemfile"],
      "Composer": ["composer.json"],
    };

    const detected = [];

    Object.entries(buildFiles).forEach(([system, files]) => {
      files.forEach((file) => {
        const filePath = path.join(this.projectPath, file);
        if (fs.existsSync(filePath)) {
          detected.push({
            system,
            file,
            path: filePath,
          });
        }
      });
    });

    this.metrics.buildSystems = detected.map((d) => d.system);
    return detected;
  }

  // 테스트 프레임워크 감지
  detectTestFrameworks() {
    const testPatterns = {
      "Jest": "jest.config.js",
      "Mocha": "mocha.opts",
      "Pytest": "pytest.ini",
      "JUnit": "pom.xml",
      "NUnit": ".csproj",
      "Cargo Test": "Cargo.toml",
      "Go Test": "go.mod",
      "Rspec": "Gemfile",
      "PHPUnit": "phpunit.xml",
    };

    const detected = [];

    Object.entries(testPatterns).forEach(([framework, file]) => {
      const filePath = path.join(this.projectPath, file);
      if (fs.existsSync(filePath)) {
        detected.push(framework);
      }
    });

    this.metrics.testFrameworks = detected;
    return detected;
  }

  // CI/CD 시스템 감지
  detectCISystems() {
    const ciDirs = {
      "GitHub Actions": ".github/workflows",
      "GitLab CI": ".gitlab-ci.yml",
      "CircleCI": ".circleci",
      "Jenkins": "Jenkinsfile",
      "Travis CI": ".travis.yml",
      "Drone": ".drone.yml",
      "Azure Pipelines": "azure-pipelines.yml",
    };

    const detected = [];

    Object.entries(ciDirs).forEach(([ci, path_] => {
      const fullPath = path.join(this.projectPath, path_);
      if (
        fs.existsSync(fullPath) ||
        (path_.startsWith(".") && fs.existsSync(path.join(this.projectPath, path_)))
      ) {
        detected.push(ci);
      }
    });

    this.metrics.ciSystems = detected;
    return detected;
  }

  // 의존성 관리자 감지
  detectDependencyManagers() {
    const managers = {
      npm: "package.json",
      yarn: "yarn.lock",
      pnpm: "pnpm-lock.yaml",
      maven: "pom.xml",
      gradle: "build.gradle",
      pip: "requirements.txt",
      poetry: "poetry.lock",
      cargo: "Cargo.lock",
      composer: "composer.lock",
      bundler: "Gemfile.lock",
    };

    const detected = [];

    Object.entries(managers).forEach(([manager, file]) => {
      const filePath = path.join(this.projectPath, file);
      if (fs.existsSync(filePath)) {
        detected.push(manager);
      }
    });

    return detected;
  }

  // 디렉토리 레이아웃 분석
  analyzeDirectoryLayout() {
    const layout = {};
    const maxDepth = 2;

    const walk = (dir, depth = 0, prefix = "") => {
      if (depth > maxDepth) return;

      try {
        const items = fs.readdirSync(dir);
        items
          .filter((item) => !item.startsWith("."))
          .forEach((item) => {
            const fullPath = path.join(dir, item);
            const stat = fs.statSync(fullPath);

            if (stat.isDirectory()) {
              const key = prefix ? `${prefix}/${item}` : item;
              layout[key] = { type: "dir", files: 0 };
              walk(fullPath, depth + 1, key);
            } else if (depth < maxDepth) {
              const parentKey = prefix || "root";
              if (!layout[parentKey]) layout[parentKey] = { type: "dir", files: 0 };
              layout[parentKey].files++;
            }
          });
      } catch {}
    };

    walk(this.projectPath);
    return layout;
  }

  // 구조 표시
  displayStructure() {
    console.log("🌍 감지된 언어:");
    this.projectStructure.languages.forEach((lang) => {
      console.log(`  • ${lang.name} (${lang.fileCount} 파일)`);
    });

    console.log("\n🔨 빌드 시스템:");
    this.projectStructure.buildSystems.forEach((build) => {
      console.log(`  • ${build.system} (${build.file})`);
    });

    console.log("\n🧪 테스트 프레임워크:");
    if (this.projectStructure.testFrameworks.length > 0) {
      this.projectStructure.testFrameworks.forEach((test) => {
        console.log(`  • ${test}`);
      });
    } else {
      console.log("  • (없음 - 테스트 추가 권장)");
    }

    console.log("\n🚀 CI/CD 시스템:");
    if (this.projectStructure.ciSystems.length > 0) {
      this.projectStructure.ciSystems.forEach((ci) => {
        console.log(`  • ${ci}`);
      });
    } else {
      console.log("  • (없음 - CI/CD 설정 권장)");
    }

    console.log("\n📦 의존성 관리자:");
    this.projectStructure.dependencyManagers.forEach((dm) => {
      console.log(`  • ${dm}`);
    });
  }

  // ========== Claude API 분석 ==========
  async analyzeWithClaude() {
    console.log("\n🤖 Claude AI로 하네스 구조 분석 중...\n");

    const prompt = this.buildAnalysisPrompt();

    const message = await client.messages.create({
      model: "claude-opus-4-6",
      max_tokens: 3000,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    const responseText = message.content[0].text;
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);

    if (jsonMatch) {
      try {
        this.analysisResult = JSON.parse(jsonMatch[0]);
        return this.analysisResult;
      } catch (e) {
        console.error("JSON 파싱 오류:", e.message);
        return { text: responseText };
      }
    }

    return { text: responseText };
  }

  buildAnalysisPrompt() {
    return `
당신은 멀티 언어 프로젝트의 빌드 하네스 및 엔지니어링 구조 전문가입니다.

다음 프로젝트 구조를 분석하고 효율화 권장사항을 제시하세요:

## 프로젝트 메타데이터
- 위치: ${this.projectPath}
- 사용 언어: ${this.projectStructure.languages.map((l) => l.name).join(", ")}
- 빌드 시스템: ${this.projectStructure.buildSystems.map((b) => b.system).join(", ")}
- 테스트 프레임워크: ${this.projectStructure.testFrameworks.join(", ") || "없음"}
- CI/CD: ${this.projectStructure.ciSystems.join(", ") || "없음"}
- 의존성 관리자: ${this.projectStructure.dependencyManagers.join(", ")}

## 디렉토리 구조
${JSON.stringify(this.projectStructure.projectLayout, null, 2)}

다음 관점에서 분석하세요:

1. **빌드 하네스 효율화**
   - 멀티 언어 빌드 순서 최적화
   - 병렬 빌드 가능성
   - 캐싱 전략

2. **의존성 관리**
   - 중복 의존성 제거
   - 버전 호환성 검토
   - 보안 취약점

3. **테스트 자동화**
   - 테스트 커버리지
   - 테스트 병렬화
   - CI/CD 통합

4. **공통 구조화**
   - 모놀리식 vs 멀티 리포 구조
   - 공유 라이브러리 기회
   - 마이크로서비스 분리

5. **개발자 생산성**
   - 로컬 개발 환경 설정
   - 빌드 시간 단축
   - 문서화

응답 형식 (JSON):
{
  "summary": "전체 요약",
  "buildOptimizations": [
    {
      "area": "빌드 하네스",
      "issue": "현재 문제",
      "recommendation": "권장사항",
      "priority": "high|medium|low",
      "estimatedSavings": "예상 절감 시간 또는 이득"
    }
  ],
  "dependencyOptimizations": [
    {
      "issue": "의존성 문제",
      "recommendation": "해결책",
      "priority": "high|medium|low"
    }
  ],
  "testingImprovements": [
    {
      "area": "테스트 영역",
      "recommendation": "개선사항",
      "priority": "high|medium|low"
    }
  ],
  "cicdImprovements": [
    {
      "area": "CI/CD 개선",
      "recommendation": "권장사항",
      "priority": "high|medium|low"
    }
  ],
  "structuralImprovements": [
    {
      "area": "구조 개선",
      "recommendation": "권장사항",
      "priority": "high|medium|low"
    }
  ],
  "implementation_roadmap": [
    {
      "phase": "Phase 1",
      "duration": "기간",
      "tasks": ["작업 1", "작업 2"]
    }
  ],
  "estimated_improvement": "전체 개선 효과 (%)"
}
    `;
  }

  // ========== 리포트 생성 ==========
  generateReport() {
    if (!this.analysisResult) {
      console.error("분석 결과가 없습니다.");
      return;
    }

    const report = `# 🔧 멀티 언어 프로젝트 하네스 엔지니어링 최적화 리포트

**프로젝트**: ${path.basename(this.projectPath)}
**생성 시간**: ${new Date().toLocaleString("ko-KR")}
**분석 방식**: Claude AI 기반 구조 분석

## 📊 프로젝트 개요

### 사용 언어
${this.projectStructure.languages.map((l) => `- ${l.name}: ${l.fileCount} 파일`).join("\n")}

### 빌드 시스템
${this.projectStructure.buildSystems.map((b) => `- ${b.system}`).join("\n") || "- (없음)"}

### 테스트 프레임워크
${this.projectStructure.testFrameworks.map((t) => `- ${t}`).join("\n") || "- (없음)"}

### CI/CD 시스템
${this.projectStructure.ciSystems.map((c) => `- ${c}`).join("\n") || "- (없음)"}

## 🎯 전체 요약
${this.analysisResult.summary || "분석 중"}

**예상 전체 개선 효과**: ${this.analysisResult.estimated_improvement || "분석 중"}

---

## 🏗️ 빌드 하네스 최적화

${
  this.analysisResult.buildOptimizations
    ?.map(
      (opt, i) => `
### ${i + 1}. ${opt.area}
- **현재 문제**: ${opt.issue}
- **우선순위**: ${opt.priority.toUpperCase()}
- **권장사항**: ${opt.recommendation}
- **예상 절감**: ${opt.estimatedSavings}
  `
    )
    .join("\n") || "분석 중"
}

---

## 📦 의존성 관리 최적화

${
  this.analysisResult.dependencyOptimizations
    ?.map(
      (opt, i) => `
### ${i + 1}. ${opt.issue}
- **우선순위**: ${opt.priority.toUpperCase()}
- **해결책**: ${opt.recommendation}
  `
    )
    .join("\n") || "분석 중"
}

---

## 🧪 테스트 자동화 개선

${
  this.analysisResult.testingImprovements
    ?.map(
      (opt, i) => `
### ${i + 1}. ${opt.area}
- **우선순위**: ${opt.priority.toUpperCase()}
- **권장사항**: ${opt.recommendation}
  `
    )
    .join("\n") || "분석 중"
}

---

## 🚀 CI/CD 파이프라인 개선

${
  this.analysisResult.cicdImprovements
    ?.map(
      (opt, i) => `
### ${i + 1}. ${opt.area}
- **우선순위**: ${opt.priority.toUpperCase()}
- **권장사항**: ${opt.recommendation}
  `
    )
    .join("\n") || "분석 중"
}

---

## 🏛️ 구조적 개선

${
  this.analysisResult.structuralImprovements
    ?.map(
      (opt, i) => `
### ${i + 1}. ${opt.area}
- **우선순위**: ${opt.priority.toUpperCase()}
- **권장사항**: ${opt.recommendation}
  `
    )
    .join("\n") || "분석 중"
}

---

## 📅 구현 로드맵

${
  this.analysisResult.implementation_roadmap
    ?.map(
      (phase) => `
### ${phase.phase}
**기간**: ${phase.duration}

${phase.tasks.map((task) => `- [ ] ${task}`).join("\n")}
  `
    )
    .join("\n") || "분석 중"
}

---

## 🎓 권장 다음 단계

1. **Phase 1 작업 시작**: 가장 높은 우선순위 항목부터 구현
2. **팀 검토**: 구조 변경 사항 팀과 논의
3. **점진적 도입**: 한 번에 하나씩 변경 적용
4. **성과 측정**: 빌드 시간, 테스트 커버리지 등 모니터링

---

*이 리포트는 Claude AI에 의해 생성되었습니다.*
*정기적으로 재분석하여 개선 진행 상황을 추적하세요.*
    `;

    const reportPath = path.join(
      this.projectPath,
      "HARNESS_OPTIMIZATION_REPORT.md"
    );
    fs.writeFileSync(reportPath, report);
    console.log(`\n📄 리포트 저장: ${reportPath}`);

    return reportPath;
  }

  // ========== Git 관리 ==========
  gitCommit(message) {
    try {
      console.log("\n📝 Git 커밋 중...");
      execSync("git add .", { cwd: this.projectPath });
      execSync(`git commit -m "${message}"`, { cwd: this.projectPath });
      console.log("✅ 커밋 완료");
      return true;
    } catch (error) {
      console.error("❌ 커밋 실패:", error.message);
      return false;
    }
  }

  gitPush() {
    try {
      console.log("🚀 푸시 중...");
      execSync("git push origin HEAD", { cwd: this.projectPath });
      console.log("✅ 푸시 완료");
      return true;
    } catch (error) {
      console.error("❌ 푸시 실패:", error.message);
      return false;
    }
  }

  // ========== 메인 실행 ==========
  async run(options = {}) {
    console.log(
      `\n🔧 멀티 언어 하네스 엔지니어링 최적화 시작\n📁 프로젝트: ${this.projectPath}\n`
    );

    try {
      // 1. 구조 분석
      this.analyzeProjectStructure();

      // 2. Claude 분석
      await this.analyzeWithClaude();

      // 3. 리포트 생성
      this.generateReport();

      // 4. Git 커밋 (선택)
      if (options.commit) {
        const message = `🔧 optimize: harness engineering structure improvements`;
        this.gitCommit(message);

        if (options.push) {
          this.gitPush();
        }
      }

      console.log("\n✨ 분석 완료!\n");
      return this.analysisResult;
    } catch (error) {
      console.error("\n❌ 오류:", error);
      process.exit(1);
    }
  }
}

// ========== CLI 실행 ==========
async function main() {
  const args = process.argv.slice(2);

  const projectPath =
    args[args.indexOf("--project") + 1] || process.cwd();
  const analyze = args.includes("--analyze");
  const optimize = args.includes("--optimize");
  const commit = args.includes("--commit");
  const push = args.includes("--push");

  const optimizer = new HarnessOptimizer(projectPath);
  await optimizer.run({
    analyze: analyze || optimize,
    commit,
    push,
  });
}

main();

module.exports = HarnessOptimizer;
