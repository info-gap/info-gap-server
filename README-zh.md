# 信息差

[English](README.md) **中文**

你知道你想看什么样的论文，但传统搜索引擎不了解你，AI 搜索为了效率总是草草了事。要是有人能沉下心来尝试每一种检索词，阅读每篇文章并判断是否符合你的要求，该有多好！

「信息差」便是一个这样的 AI 智能体！该智能体可以在 LLaMA3-8b 级别的大模型上运行。得益于严格的输出类型规范，「信息差」可以以较高的质量不断向你推荐符合要求的文章。

## 使用方法

目前只支持 Ollama、LiteLLM 或其他 OpenAI 格式的接口。我设计的提示对模型要求不高，水平在 LLaMA3-8b 附近即可，但会消耗大量的 token，因此建议使用自建接口，避免过高的消费。

目前本仓库还在开发阶段，暂未封装 Docker 镜像。如果需要使用，请先克隆本仓库：

```
git clone git@github.com:info-gap/info-gap-server.git
```

然后安装 Python 依赖：

```
instructor
arxiv
```

创建 `.env` 并设置：

```
OPENAI_API_URL=<your-api-url>
OPENAI_API_KEY=<your-api-key> # 无密码的话可以写任意东西
```

## 开发计划

- [ ] 分页查询
- [ ] 模块性能测试
- [ ] 优化提示
- [ ] Docker 封装和自定义 LLM
- [ ] 客户端

## 代码结构

暂时都在 [main.py](main.py) 里面，写了很多注释，应该相对简明易懂。

我用了 [Instructor](https://github.com/jxnl/instructor) 库来把对 LLM 输出的限制编码在类型里面。其中 `RelevantProof` 的实现参考了依值类型中的相等类型，即 `RelevantProof(article, request)` 表示 `article` 和 `request` 相关的证明。