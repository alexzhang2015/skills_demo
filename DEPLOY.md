# 腾讯云 CloudBase 部署指南

## 部署方式

### 方式一：压缩包上传（推荐）

1. **打包项目**
   ```bash
   # 在项目根目录执行
   zip -r skills-demo.zip . -x "*.git*" -x "*__pycache__*" -x "*.venv*" -x "*.pytest_cache*" -x "workspace/*" -x "*.env*"
   ```

2. **上传到腾讯云**
   - 登录 [腾讯云 CloudBase 控制台](https://console.cloud.tencent.com/tcb)
   - 进入「云托管」
   - 点击「新建服务」→「本地代码部署」
   - 代码包类型选择「压缩包」
   - 上传 `skills-demo.zip`

3. **配置服务**
   - 服务名称：`skills-demo`（小写字母、数字、连字符）
   - 服务端口：`80`
   - 访问端口：`80`

4. **环境变量设置**（在「环境变量设置」中配置）
   ```
   LLM_PROVIDER=claude
   ANTHROPIC_API_KEY=sk-ant-xxx
   # 或其他 Provider
   # OPENAI_API_KEY=sk-xxx
   # GOOGLE_API_KEY=xxx
   ```

### 方式二：Docker 镜像

1. **本地构建镜像**
   ```bash
   docker build -t skills-demo:latest .
   ```

2. **推送到腾讯云容器镜像服务**
   ```bash
   # 登录腾讯云镜像仓库
   docker login ccr.ccs.tencentyun.com -u <账号ID>

   # 标记镜像
   docker tag skills-demo:latest ccr.ccs.tencentyun.com/<命名空间>/skills-demo:latest

   # 推送镜像
   docker push ccr.ccs.tencentyun.com/<命名空间>/skills-demo:latest
   ```

3. **在云托管中选择镜像部署**

## 本地测试 Docker

```bash
# 构建
docker build -t skills-demo:latest .

# 运行
docker run -p 8080:80 \
  -e LLM_PROVIDER=claude \
  -e ANTHROPIC_API_KEY=sk-ant-xxx \
  skills-demo:latest

# 访问 http://localhost:8080
```

## 服务配置建议

| 配置项 | 推荐值 | 说明 |
|-------|--------|------|
| CPU | 1 核 | 轻量应用足够 |
| 内存 | 1 GB | 根据并发调整 |
| 实例数 | 1-3 | 按需扩缩容 |
| 端口 | 80 | 默认 HTTP 端口 |

## 环境变量

| 变量名 | 必需 | 说明 |
|-------|------|------|
| `LLM_PROVIDER` | 否 | LLM 提供商：claude/openai/gemini/ollama |
| `ANTHROPIC_API_KEY` | 条件 | Claude API Key |
| `OPENAI_API_KEY` | 条件 | OpenAI API Key |
| `GOOGLE_API_KEY` | 条件 | Gemini API Key |
| `DATABASE_URL` | 否 | 数据库连接（默认 SQLite） |

## 健康检查

服务提供健康检查端点：
- `GET /api/status` - 返回服务状态

## 常见问题

### Q: 部署后无法访问？
检查服务端口是否配置为 80，访问端口也是 80。

### Q: API 调用失败？
检查环境变量中的 API Key 是否正确配置。

### Q: 如何查看日志？
在云托管控制台「日志监控」中查看运行日志。
