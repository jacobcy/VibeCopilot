# VibeCopilot 应用流程设计

本文档通过流程图和数据流图详细说明VibeCopilot的应用工作流程，展示最终用户将如何使用该产品。

## 1. 多工具连接流程

### 1.1 系统初始化流程

```mermaid
flowchart TD
    A[开始] --> B{首次使用?}
    B -->|是| C[工具检测]
    B -->|否| D[加载配置]
    C --> E[扫描安装工具]
    E --> F{检测到工具}
    F -->|Cursor| G[配置Cursor连接]
    F -->|Obsidian| H[配置Obsidian连接]
    F -->|GitHub工具| I[配置GitHub连接]
    G --> J[验证连接]
    H --> J
    I --> J
    D --> K[同步工具状态]
    J --> L[创建配置文件]
    L --> K
    K --> M[完成初始化]
```

### 1.2 文档与知识库同步流程

```mermaid
flowchart TD
    A[开始] --> B[检测文档变更]
    B --> C{变更类型}
    C -->|新文档| D[应用文档模板]
    C -->|修改文档| E[获取文档差异]
    C -->|删除文档| F[标记同步删除]
    D --> G[准备Obsidian同步]
    E --> G
    F --> G
    G --> H{同步方向}
    H -->|VibeCopilot → Obsidian| I[转换为Obsidian格式]
    H -->|Obsidian → VibeCopilot| J[转换为标准格式]
    I --> K[写入Obsidian库]
    J --> L[更新本地文档]
    K --> M[标记同步完成]
    L --> M
    M --> N{需要Docusaurus同步?}
    N -->|是| O[筛选公开内容]
    N -->|否| P[结束]
    O --> Q[转换为Docusaurus格式]
    Q --> R[部署到展示站点]
    R --> P
```

### 1.3 GitHub集成流程

```mermaid
flowchart TD
    A[开始] --> B[获取项目配置]
    B --> C[连接GitHub API]
    C --> D{操作类型}
    D -->|项目结构分析| E[调用gitdiagram]
    D -->|Issue管理| F[使用Octokit API]
    D -->|文档同步| G[双向同步处理]
    E --> H[生成架构图表]
    F --> I[处理Issue关联]
    G --> J[处理PR和文档关联]
    H --> K[更新文档]
    I --> L[更新任务状态]
    J --> M[合并变更]
    K --> N[完成GitHub操作]
    L --> N
    M --> N
```

## 2. 主要数据流程

### 2.1 AI代理规则与文档流

```mermaid
flowchart TD
    A[文档模板系统] --> B[规则生成器]
    B --> C[Cursor规则文件]
    C --> D[Cursor自定义代理]
    D --> E[AI生成内容]
    E --> F[内容处理器]
    F --> G[文档更新]
    G --> A
    G --> H[Obsidian同步]
    H --> I[Obsidian知识库]
    I --> J[知识检索接口]
    J --> B
```

### 2.2 项目数据整合流

```mermaid
flowchart LR
    A[GitHub仓库] --> B[Octokit API]
    C[项目文件] --> D[gitdiagram]
    D --> E[架构分析]
    B --> F[项目数据聚合器]
    E --> F
    F --> G[集成数据模型]
    G --> H[文档生成器]
    G --> I[可视化引擎]
    H --> J[更新文档]
    I --> K[生成报告和图表]
    J --> L[同步到Obsidian]
    K --> M[集成到Docusaurus]
```

## 3. 工具交互流程

### 3.1 Cursor自定义代理集成

```mermaid
flowchart TD
    A[开始] --> B[分析开发任务]
    B --> C[选择适合的AI代理]
    C --> D[加载相关规则]
    D --> E[从Obsidian获取上下文]
    E --> F[构建完整提示词]
    F --> G[提交给Cursor]
    G --> H[接收AI输出]
    H --> I[验证输出质量]
    I --> J{符合要求?}
    J -->|是| K[应用变更]
    J -->|否| L[调整规则]
    L --> F
    K --> M[更新文档]
    M --> N[同步到知识库]
    N --> O[结束]
```

### 3.2 Obsidian知识库同步

```mermaid
flowchart TD
    A[监听文件变更] --> B{变更来源}
    B -->|VibeCopilot| C[准备Obsidian写入]
    B -->|Obsidian| D[准备本地更新]
    C --> E[转换元数据和链接]
    D --> F[处理Obsidian特性]
    E --> G[写入Obsidian]
    F --> H[更新本地文件]
    G --> I[维护关系图谱]
    H --> I
    I --> J[更新索引]
    J --> K[完成同步]
```

### 3.3 Docusaurus展示系统

```mermaid
flowchart TD
    A[监听标记为公开的文档] --> B[过滤敏感内容]
    B --> C[组织文档结构]
    C --> D[生成导航菜单]
    D --> E[处理内部链接]
    E --> F[转换为Docusaurus格式]
    F --> G[添加元数据]
    G --> H[生成静态资源]
    H --> I[部署更新]
    I --> J[完成发布]
```

## 4. 跨工具数据流

```mermaid
flowchart LR
    A[文档系统] --> B[文档处理器]
    B --> C[数据转换层]
    C -->|Obsidian格式| D[Obsidian适配器]
    C -->|Cursor规则| E[Cursor适配器]
    C -->|GitHub数据| F[GitHub适配器]
    C -->|Docusaurus| G[Docusaurus适配器]
    D --> H[Obsidian知识库]
    E --> I[Cursor自定义代理]
    F --> J[GitHub项目]
    G --> K[Docusaurus站点]
    H --> L[双向同步控制器]
    I --> L
    J --> L
    K --> L
    L --> A
```

## 5. 用户交互场景

### 5.1 开发者工作流程

1. 开发者连接工具并初始化VibeCopilot配置
2. 项目文档自动同步到Obsidian知识库
3. 开发者基于gitdiagram生成的架构图表理解项目
4. 使用预配置的Cursor代理规则进行开发
5. 文档与GitHub Issues保持双向关联
6. PR创建时自动关联相关文档
7. 知识和经验自动积累在Obsidian中
8. 精选内容发布到Docusaurus供团队参考

### 5.2 团队协作流程

1. 项目管理者在GitHub Projects创建任务
2. 任务自动与文档关联并反映在知识库中
3. 开发者使用标准化提示词模板与AI工具协作
4. 团队在Obsidian中共享和优化知识
5. 通过Docusaurus访问公开的最佳实践
6. GitHub状态变化自动反映在文档系统
7. 新成员通过Docusaurus快速了解项目
8. 跨项目知识在Obsidian中积累并共享

## 6. 工具整合配置流程

```mermaid
flowchart TD
    A[开始配置] --> B[选择要整合的工具]
    B --> C{工具类型}
    C -->|Cursor| D[配置Cursor路径]
    C -->|Obsidian| E[配置Obsidian库路径]
    C -->|GitHub| F[配置GitHub凭据]
    C -->|Docusaurus| G[配置Docusaurus路径]
    D --> H[验证Cursor设置]
    E --> I[验证Obsidian连接]
    F --> J[验证GitHub访问]
    G --> K[验证Docusaurus配置]
    H --> L[设置规则目录]
    I --> M[配置同步规则]
    J --> N[设置项目关联]
    K --> O[配置部署方式]
    L --> P[保存配置]
    M --> P
    N --> P
    O --> P
    P --> Q[生成配置文件]
    Q --> R[完成配置]
```

> 注：本文档仅展示VibeCopilot应用的工作流程，项目的详细功能请参阅《功能设计》文档，开发流程请参阅《开发流程指南》文档，整体架构请参阅《项目概述》文档。
