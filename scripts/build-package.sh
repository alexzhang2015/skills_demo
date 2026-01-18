#!/bin/bash
# 构建腾讯云部署包脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 开始构建腾讯云部署包...${NC}"

# 项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 输出文件名
OUTPUT="skills-demo.zip"

# 删除旧的包
if [ -f "$OUTPUT" ]; then
    echo -e "${YELLOW}删除旧的部署包...${NC}"
    rm "$OUTPUT"
fi

# 创建压缩包
echo -e "${YELLOW}打包文件...${NC}"
zip -r "$OUTPUT" . \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "*.venv*" \
    -x "venv/*" \
    -x "*.pytest_cache*" \
    -x "workspace/*" \
    -x "*.env" \
    -x "*.env.*" \
    -x "*.DS_Store" \
    -x "*.pyc" \
    -x "*.pyo" \
    -x "*.egg-info*" \
    -x "dist/*" \
    -x "build/*" \
    -x "htmlcov/*" \
    -x ".coverage" \
    -x "*.log" \
    -x "skills-demo.zip"

# 显示包信息
echo ""
echo -e "${GREEN}✅ 部署包构建完成！${NC}"
echo ""
echo "📦 文件: $ROOT_DIR/$OUTPUT"
echo "📏 大小: $(du -h "$OUTPUT" | cut -f1)"
echo ""
echo "下一步："
echo "1. 登录腾讯云 CloudBase 控制台"
echo "2. 进入「云托管」→「新建服务」→「本地代码部署」"
echo "3. 上传 $OUTPUT"
echo "4. 配置服务端口为 80"
echo "5. 设置环境变量 (LLM_PROVIDER, API Keys 等)"
