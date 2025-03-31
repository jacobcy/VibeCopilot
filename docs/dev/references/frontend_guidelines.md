# VibeCopilot 前端开发规范

本文档定义了VibeCopilot前端开发的规范与指南，包括UI组件库选择、代码风格、目录结构、状态管理和交互模式等。

## 1. 技术栈选择

### 1.1 核心技术

- **TypeScript** - 强类型支持，提高代码质量和开发体验
- **React** - 用于构建用户界面的库
- **Tailwind CSS** - 实用优先的CSS框架
- **Vite** - 前端构建工具，提供快速的开发体验

### 1.2 UI组件库

- **Primary: shadcn/ui** - 基于Radix UI的高质量组件集合
  - 高度可定制
  - 支持暗色模式
  - 无运行时依赖
  - 可复制粘贴的组件代码

- **Secondary: Radix UI Primitives** - 用于构建自定义组件的底层库
  - 无样式但功能完备的UI原语
  - 可访问性支持
  - 支持组合和定制

### 1.3 状态管理

- **Zustand** - 轻量级状态管理库
  - 简单直观的API
  - 基于钩子的用法
  - 良好的TypeScript支持
  - 支持中间件（如持久化、日志等）

- **React Query** - 用于服务器状态管理
  - 数据获取和缓存
  - 自动重试和轮询
  - 乐观更新支持

### 1.4 其他工具

- **React Router** - 客户端路由
- **React Hook Form** - 表单处理
- **Zod** - 数据验证
- **date-fns** - 日期处理
- **Monaco Editor** - 代码编辑器组件（用于AI提示词编辑等）

## 2. 目录结构规范

```
src/
├── ui/
│   ├── components/        # 共享UI组件
│   │   ├── common/        # 基础组件（按钮、输入框等）
│   │   ├── layout/        # 布局组件
│   │   ├── dashboard/     # 仪表盘相关组件
│   │   ├── project/       # 项目管理相关组件
│   │   ├── document/      # 文档相关组件
│   │   ├── ai/            # AI交互相关组件
│   │   └── tools/         # 工具推荐相关组件
│   ├── hooks/             # 自定义React钩子
│   ├── styles/            # 全局样式和主题
│   ├── utils/             # UI工具函数
│   ├── contexts/          # React上下文
│   ├── providers/         # UI提供者组件
│   └── types/             # UI相关类型定义
├── pages/                 # 页面组件
│   ├── dashboard/
│   ├── project/
│   ├── documents/
│   ├── settings/
│   └── tools/
├── features/              # 功能模块
│   ├── project-init/
│   ├── workflow/
│   ├── document-gen/
│   ├── ai-integration/
│   └── tools-recommendation/
├── store/                 # 状态管理
│   ├── project-store.ts
│   ├── document-store.ts
│   ├── settings-store.ts
│   └── ui-store.ts
├── services/              # API服务和数据获取
│   ├── api-client.ts
│   ├── project-service.ts
│   ├── document-service.ts
│   └── ai-service.ts
└── mcp/                   # MCP工具界面相关
    ├── components/
    ├── hooks/
    └── mcp-client.ts
```

## 3. 命名约定

### 3.1 文件命名

- React组件文件: **PascalCase.tsx**
  - 例: `Button.tsx`, `ProjectCard.tsx`
- 钩子文件: **use-kebab-case.ts**
  - 例: `use-project-status.ts`
- 工具函数: **camelCase.ts**
  - 例: `formatDate.ts`
- 样式文件: **component-name.css**
  - 例: `button.css`
- 类型定义文件: **camelCase.types.ts**
  - 例: `project.types.ts`

### 3.2 组件命名

- 组件名: **PascalCase**
  - 例: `ProjectStatusCard`, `DocumentList`
- 组件属性: **camelCase**
  - 例: `isLoading`, `onStatusChange`
- 钩子名: **usePascalCase**
  - 例: `useProjectStatus`, `useDocumentList`
- 事件处理函数: **handle[Event]**
  - 例: `handleClick`, `handleInputChange`

### 3.3 CSS类命名

使用Tailwind CSS的工具类优先，自定义类名使用以下约定:

- 组件类: **component-name**
- 状态修饰符: **component-name--state**
- 变体: **component-name--variant**
- 子元素: **component-name__element**

## 4. 组件设计原则

### 4.1 组件分类

- **原子组件** - 最小的UI构建块（按钮、输入框等）
- **分子组件** - 由多个原子组件组成（表单控件、卡片等）
- **组织组件** - 特定功能的复杂组件（状态卡片、文档编辑器等）
- **模板组件** - 页面布局模板
- **页面组件** - 完整页面

### 4.2 组件接口原则

- 保持组件接口简单、一致
- 使用合理的默认值
- 支持UI自定义（通过props传递样式或类名）
- 提供完整的类型定义
- 使用分离的prop接口定义

```tsx
// 例: Button组件接口
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'link';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}
```

### 4.3 组件状态管理

- 本地UI状态使用`useState`或`useReducer`
- 跨组件状态使用Zustand
- 服务器数据状态使用React Query
- 全局UI状态（如主题、侧边栏状态）使用Zustand

### 4.4 组件文档要求

每个共享组件应包含以下文档注释:

```tsx
/**
 * 按钮组件
 *
 * 用于触发操作，支持多种样式变体和尺寸。
 *
 * @example
 * ```tsx
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   点击我
 * </Button>
 * ```
 *
 * @example 带图标的按钮
 * ```tsx
 * <Button icon={<PlusIcon />}>新建项目</Button>
 * ```
 */
```

## 5. 状态管理规范

### 5.1 Zustand Store结构

```typescript
// 示例: 项目状态存储
interface ProjectState {
  // 状态
  currentProject: Project | null;
  projects: Project[];
  isLoading: boolean;
  error: Error | null;

  // 动作
  loadProjects: () => Promise<void>;
  createProject: (project: ProjectInput) => Promise<void>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
  setCurrentProject: (projectId: string) => void;
}

const useProjectStore = create<ProjectState>((set, get) => ({
  // 初始状态
  currentProject: null,
  projects: [],
  isLoading: false,
  error: null,

  // 实现动作
  loadProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectService.getProjects();
      set({ projects, isLoading: false });
    } catch (error) {
      set({ error: error as Error, isLoading: false });
    }
  },
  // ...其他动作实现
}));
```

### 5.2 状态选择器模式

推荐使用选择器模式来获取状态的子集，避免不必要的重渲染:

```typescript
// 良好实践
const currentProject = useProjectStore(state => state.currentProject);
const { loadProjects } = useProjectStore(state => ({
  loadProjects: state.loadProjects
}));

// 避免
const { currentProject, projects, loadProjects } = useProjectStore();
```

### 5.3 React Query使用规范

对于服务器数据，使用React Query以获得自动缓存、加载状态等功能:

```typescript
// 查询示例
const { data: projects, isLoading, error } = useQuery({
  queryKey: ['projects'],
  queryFn: () => projectService.getProjects(),
});

// 变更示例
const mutation = useMutation({
  mutationFn: (newProject: ProjectInput) => projectService.createProject(newProject),
  onSuccess: () => {
    // 成功处理
    queryClient.invalidateQueries({ queryKey: ['projects'] });
    toast.success('项目创建成功');
  },
});
```

## 6. 交互模式规范

### 6.1 表单交互

- 使用React Hook Form处理表单状态和验证
- 使用Zod进行数据模式验证
- 实时验证显示错误信息
- 提交前进行最终验证
- 显示清晰的成功/错误反馈

```tsx
// 表单示例
function ProjectForm({ onSubmit }) {
  const schema = z.object({
    name: z.string().min(3, '项目名称至少3个字符'),
    description: z.string().optional(),
    // ...其他字段验证
  });

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema)
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* 表单内容 */}
    </form>
  );
}
```

### 6.2 加载状态处理

- 在UI中显示明确的加载状态
- 使用骨架屏或加载指示器
- 避免布局偏移(CLS)
- 对长时间操作提供进度反馈

```tsx
// 加载状态示例
function ProjectList() {
  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  if (isLoading) {
    return <ProjectListSkeleton />;
  }

  return (
    <div>
      {data.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

### 6.3 错误处理

- 表单级错误显示在相关字段旁
- 网络错误以toast或弹窗形式显示
- 提供错误恢复选项（重试、回滚等）
- 严重错误提供联系支持选项

### 6.4 交互反馈

- 操作按钮在点击后显示加载状态
- 成功操作显示确认消息
- 重要操作需要确认对话框
- 使用微动画指示状态变化

### 6.5 导航模式

- 使用面包屑指示导航路径
- 工作流导航使用步骤指示器
- 相关操作分组到下拉菜单或工具栏
- 提供返回和取消选项

## 7. 响应式设计

### 7.1 断点定义

```typescript
// 断点定义
const breakpoints = {
  sm: '640px',   // 小屏幕手机
  md: '768px',   // 大屏幕手机/小平板
  lg: '1024px',  // 平板/小笔记本
  xl: '1280px',  // 桌面
  '2xl': '1536px' // 大桌面
};
```

### 7.2 响应式策略

- 使用移动优先设计方法
- 通过Tailwind CSS类处理响应式样式
- 在小屏幕上简化界面
- 确保触摸友好的交互目标大小
- 适当使用栅格和弹性布局

```tsx
// 响应式组件示例
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {projects.map(project => (
    <ProjectCard key={project.id} project={project} />
  ))}
</div>
```

### 7.3 MCP工具响应性

对于MCP工具界面:
- 设计为适应不同大小的面板
- 支持折叠/展开视图
- 提供精简模式和详细模式

## 8. 可访问性指南

### 8.1 基本要求

- 所有交互元素可通过键盘访问
- 提供有意义的替代文本
- 使用适当的ARIA属性
- 确保足够的颜色对比度
- 支持屏幕阅读器

### 8.2 表单可访问性

- 为每个表单控件提供标签
- 用`fieldset`和`legend`组织相关控件
- 错误消息与相关字段关联
- 使用`aria-invalid`标记无效输入

### 8.3 键盘导航

- 使用逻辑Tab顺序
- 提供键盘快捷键
- 确保焦点指示器清晰可见
- 实现适当的焦点管理

## 9. 性能优化

### 9.1 渲染优化

- 避免不必要的渲染
- 使用`React.memo`、`useMemo`和`useCallback`
- 应用代码分割和懒加载
- 优化大型列表渲染

### 9.2 资源优化

- 优化图像大小和格式
- 使用代码分割减小包大小
- 延迟加载非关键资源
- 实现缓存策略

## 10. 主题与样式

### 10.1 色彩系统

- **主要色**: `#2563eb` (蓝色)
- **次要色**: `#475569` (石板灰)
- **成功色**: `#22c55e` (绿色)
- **警告色**: `#f59e0b` (琥珀色)
- **危险色**: `#ef4444` (红色)
- **中性色**:
  - 背景: `#ffffff` (白色) / `#0f172a` (暗色模式)
  - 文本: `#1e293b` (暗灰) / `#f8fafc` (暗色模式)
  - 边框: `#e2e8f0` (淡灰) / `#334155` (暗色模式)

### 10.2 排版

- **主要字体**: Inter, system-ui, sans-serif
- **代码字体**: JetBrains Mono, monospace
- **基础大小**: 16px
- **标题大小**:
  - h1: 2.25rem (36px)
  - h2: 1.875rem (30px)
  - h3: 1.5rem (24px)
  - h4: 1.25rem (20px)
  - h5: 1.125rem (18px)
  - h6: 1rem (16px)

### 10.3 间距系统

使用Tailwind CSS的间距系统，基于0.25rem (4px)的倍数。

### 10.4 暗色模式

- 支持通过操作系统偏好自动切换
- 允许用户手动选择
- 确保所有组件支持暗色模式

```tsx
// 主题提供者示例
function ThemeProvider({ children }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // 检测系统偏好
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(prefersDark ? 'dark' : 'light');
  }, []);

  return (
    <div className={theme === 'dark' ? 'dark' : ''}>
      <div className="bg-white text-gray-900 dark:bg-gray-900 dark:text-white">
        {children}
      </div>
    </div>
  );
}
```

## 11. 代码质量与测试

### 11.1 Linting与格式化

- 使用ESLint进行代码质量检查
- 使用Prettier进行代码格式化
- 强制执行TypeScript类型检查

### 11.2 组件测试

- 使用React Testing Library进行组件测试
- 编写单元测试和集成测试
- 测试关键用户流程
- 确保适当的测试覆盖率

### 11.3 CI/CD集成

- 在PR前运行测试和代码检查
- 自动化部署流程
- 性能基准测试

这些前端规范应在项目开发过程中严格遵循，以保持代码质量和一致性。规范可能会随项目进展进行更新和完善。
