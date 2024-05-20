# Info Gap

**English** [中文](README-zh.md)

An AI daemon for arXiv paper searching. Time and token count is traded for low model requirement, response length and quality.

## Getting started

For now, only OpenAI-format API is supported. To get started, first clone the repo:

```
git clone git@github.com:info-gap/info-gap-server.git
```

Install these python dependencies:

```
instructor
arxiv
```

Create `.env` and set:

```
OPENAI_API_URL=<your-api-url>
OPENAI_API_KEY=<your-api-key> # Can be arbitrary if no password
```

Modify `REQUEST` in `main.py`, and run agent:

```
python main.py
```
