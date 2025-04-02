# 项目架构图

```mermaid
flowchart TD
    subgraph Project_Structure["VibeCopilot Project Structure"]
        style Project_Structure fill:#f9f,stroke:#333,stroke-width:2px
        .cursor["Cursor AI配置"]:::config
        docs["文档目录"]:::directory
        modules["模块"]:::module
        scripts["脚本"]:::script
        tools["工具指南"]:::guide
        templates["项目模板"]:::template
        src["源代码"]:::source

        click .cursor ".cursor"
        click docs "docs"
        click modules "modules"
        click scripts "scripts"
        click tools "docs/shared/prompts"
        click templates "docs/shared/templates"
        click src "src"

        subgraph Modules["集成的外部模块"]
            style Modules fill:#bbf,stroke:#333,stroke-width:2px
            cursor_generator["Cursor规则生成器"]:::submodule
            gitdiagram["GitDiagram"]:::submodule
            obsidiosaurus["Obsidiosaurus"]:::submodule

            click cursor_generator "modules/cursor-custom-agents-rules-generator"
            click gitdiagram "modules/gitdiagram"
            click obsidiosaurus "modules/obsidiosaurus"
        end

        modules --> cursor_generator
        modules --> gitdiagram
        modules --> obsidiosaurus
    end

    docs -->|生成文档| scripts
    docs -->|包含| tools
    docs -->|包含| templates
    .cursor -->|集成| modules
    modules -->|可视化| gitdiagram
    src -->|核心功能| modules
```

<style>
    .config { fill: #ffcc00; }
    .directory { fill: #66ccff; }
    .module { fill: #99ff99; }
    .script { fill: #ff9999; }
    .guide { fill: #ffccff; }
    .template { fill: #ffff99; }
    .source { fill: #ffccff; }
    .submodule { fill: #ccffcc; }
</style>
```
