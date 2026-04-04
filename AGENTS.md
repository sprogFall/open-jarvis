# Repository Instructions

- 以根目录的`设计文档.md`作为本仓库初始化阶段的唯一设计基准。
- 当前目录必须维护三个一等模块：`gateway`、`client`、`app`。
- 本阶段目标是先完成基础能力闭环：任务下发、客户端执行、敏感操作审批、审批后恢复、实时日志、离线待处理恢复。
- 开发策略必须遵循 TDD：先写失败测试，再补实现，最后回归测试。
- 交付优先级是“三端交互正常”与“功能基本完善”，不要为了未来可能需求过度抽象。
- 扩展性要求保持克制：只在协议、状态机、技能接口、存储层预留清晰边界，不预建复杂插件市场、分布式调度、或多租户体系。
- 修改任一模块时，都必须同步检查三端协议契约与测试是否仍然成立。
- Python 测试使用`pytest`，Flutter 测试使用`flutter test`。

## Dashboard 前端开发规范

- `dashboard` 是独立静态前端项目，构建产物必须可通过 `npm run build` 输出到 `dist/`，不能重新耦合回 Gateway 模板渲染。
- Dashboard 默认按“静态资源子路径 + API 子路径”部署设计，必须兼容如 `xx.com/jarvis/dashboard` 与 `xx.com/jarvis/api` 的组合。
- 目录分层保持稳定：
  - `src/app` 只放应用装配、页面级状态编排、全局模型，不直接堆业务视图。
  - `src/features` 按业务域拆分，如 `auth`、`devices`、`skills`、`tasks`、`overview`、`settings`。
  - `src/components` 只放跨 feature 复用的通用组件。
  - `src/lib` 放格式化、存储、解析、请求辅助等无业务归属的工具。
- App.tsx 保持薄，只负责入口装配、登录态切换或顶层壳体组合，不再承载具体业务 CRUD、长表单、表格渲染与轮询逻辑。
- 单个 feature 内部优先内聚：设备相关弹层、表格、表单与动作放在 `features/devices`，不要散落到全局目录。
- 页面级副作用（初始化拉数、轮询、跨 feature 刷新、鉴权失效处理）统一收敛在 `src/app` 层的 controller/hook 中，不要分散到多个 tab 组件里各自重复实现。
- 展示组件尽量纯函数化，通过 props 接收数据和动作；只有在明确属于页面编排职责时，才允许直接访问全局 controller。
- Dashboard 页面文案必须聚焦当前业务操作与结果反馈，不要展示实现细节、数据来源限制、环境变量回显策略、写入路径等业务无关说明；这类约束通过交互、协议与测试保证，不要堆在页面提示里。
- Dashboard 的弹层、抽屉、长表单与长列表必须保证内容完整可见，不能出现内容被裁切、操作区不可达或已分配数据看不全的问题；必要时提供内部滚动，并优先在通用容器层统一兜底。
- 新增前端能力时，优先补结构或行为测试，再改实现；至少保证 `pytest gateway/tests -q` 中与 dashboard 相关测试和 `cd dashboard && npm run build` 通过。
- 更新 Dashboard 部署方式、环境变量或 API 基地址规则时，必须同步更新本地中文文档，至少包括 `dashboard/README.md` 或 `dashboard/DEPLOYMENT.md`。
