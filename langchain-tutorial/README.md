# LangChain 保姆级学习路线（由浅入深 + 实战项目）

> 作者：柒月 🌸 | 整理时间：2026-04-22
> 适用人群：有 Python 基础，想学习 AI 应用开发的开发者
> 学习周期：约 2-3 周（每天 2-3 小时）

---

## 目录

- [一、LangChain 是什么？](#一langchain-是什么)
- [二、前置知识](#二前置知识)
- [三、环境搭建](#三环境搭建)
- [四、阶段一：核心概念（Day 1-3）](#四阶段一核心概念day-1-3)
  - [4.1 Model I/O：模型输入输出](#41-model-io模型输入输出)
  - [4.2 LCEL：LangChain 表达式语言](#42-lcellangchain-表达式语言)
  - [4.3 Prompt 提示词工程](#43-prompt-提示词工程)
- [五、阶段二：数据连接（Day 4-6）](#五阶段二数据连接day-4-6)
  - [5.1 Document Loaders 文档加载器](#51-document-loaders-文档加载器)
  - [5.2 Text Splitters 文本切分器](#52-text-splitters-文本切分器)
  - [5.3 Embeddings 向量嵌入](#53-embeddings-向量嵌入)
  - [5.4 Vector Stores 向量存储](#54-vector-stores-向量存储)
  - [5.5 Retrievers 检索器](#55-retrievers-检索器)
- [六、阶段三：RAG 检索增强生成（Day 7-9）](#六阶段三rag-检索增强生成day-7-9)
  - [6.1 什么是 RAG？](#61-什么是-rag)
  - [6.2 RAG 完整实现](#62-rag-完整实现)
  - [6.3 RAG 进阶技巧](#63-rag-进阶技巧)
- [七、阶段四：Agent 智能体（Day 10-12）](#七阶段四agent-智能体day-10-12)
  - [7.1 什么是 Agent？](#71-什么是-agent)
  - [7.2 Tools 工具定义](#72-tools-工具定义)
  - [7.3 Agent 实现](#73-agent-实现)
  - [7.4 LangGraph 进阶](#74-langgraph-进阶)
- [八、阶段五：Memory 记忆（Day 13-14）](#八阶段五memory-记忆day-13-14)
- [九、实战项目](#九实战项目)
  - [项目一：个人知识库问答助手（入门）](#项目一个人知识库问答助手入门)
  - [项目二：AI 客服机器人（中级）](#项目二ai-客服机器人中级)
  - [项目三：自动研究报告生成器（高级）](#项目三自动研究报告生成器高级)
- [十、参考资源](#十参考资源)

---

## 一、LangChain 是什么？

**LangChain** 是一个开源框架，用于快速构建基于大语言模型（LLM）的 AI 应用。它提供了一套标准化的接口和组件，让你不用从零开始就能开发强大的 AI 应用。

### 核心价值

1. **统一模型接口**：一行代码切换 OpenAI / Claude / Gemini / 智谱 / 本地模型，不会被某个厂商锁定
2. **模块化组件**：提示词模板、文档加载、向量存储、工具调用等都是独立模块，按需组合
3. **Agent 智能体**：让 AI 自主思考、调用工具、完成复杂任务
4. **RAG 检索增强**：让 AI 基于你自己的文档回答问题，解决幻觉问题
5. **LCEL 链式编排**：像搭积木一样组合各种组件

### LangChain 生态系统

| 组件 | 说明 |
|------|------|
| **LangChain** | 核心框架，提供基础抽象和链式编排 |
| **LangGraph** | 底层 Agent 编排框架，用于复杂工作流 |
| **LangSmith** | 调试、追踪、评估平台 |
| **LangServe** | 将链部署为 REST API |
| **Deep Agents** | 开箱即用的高级 Agent 实现 |

### 一句话理解 LangChain

> LangChain 就是 **AI 应用的"乐高积木"**——它不提供大模型本身，而是提供一套标准化的方式来调用大模型、处理数据、调用工具，让你专注于业务逻辑。

---

## 二、前置知识

在开始之前，你需要掌握：

- ✅ **Python 基础**：变量、函数、类、装饰器、异步（async/await）
- ✅ **API 基础**：理解 HTTP 请求、API Key、REST 接口
- ✅ **命令行操作**：会使用 pip、venv、git
- ⭕ **了解大语言模型**：知道 GPT、Claude 等是什么（不知道也没关系，教程里会讲）
- ⭕ **有 OpenAI 或其他模型的 API Key**（可以用智谱 GLM 免费获取）

---

## 三、环境搭建

### 3.1 创建虚拟环境

```bash
# 创建项目目录
mkdir langchain-learn && cd langchain-learn

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 升级 pip
pip install --upgrade pip
```

### 3.2 安装 LangChain

```bash
# 核心包（必装）
pip install langchain langchain-core

# 模型提供商（按需安装）
pip install langchain-openai        # OpenAI / 兼容接口
pip install langchain-community      # 社区集成（含智谱等）
pip install langchain-anthropic      # Claude
pip install langchain-google-genai   # Gemini

# 文档处理
pip install pypdf                    # PDF 解析
pip install unstructured             # 非结构化文档解析

# 向量存储
pip install faiss-cpu                # FAISS 向量数据库（本地）

# 工具和 Web 界面（可选）
pip install wikipedia                # 维基百科工具
pip install duckduckgo-search        # 搜索工具
pip install gradio                   # Web UI
pip install streamlit                # 另一个 Web UI 框架
```

### 3.3 配置 API Key

```bash
# 在 ~/.bashrc 或项目根目录 .env 文件中配置
export OPENAI_API_KEY="sk-your-key-here"
# 或使用智谱（国内免费额度）
export ZHIPUAI_API_KEY="your-zhipu-key"
```

### 3.4 验证安装

```python
# test_setup.py
import langchain
print(f"LangChain 版本: {langchain.__version__}")

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke("说一句话")
print(response.content)
```

---

## 四、阶段一：核心概念（Day 1-3）

### 4.1 Model I/O：模型输入输出

这是 LangChain 最基础的模块，处理与模型的交互。

#### 4.1.1 Chat Models（聊天模型）

LangChain 统一了不同模型的调用方式：

```python
# ===== OpenAI =====
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ===== Anthropic Claude =====
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# ===== Google Gemini =====
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# ===== 智谱 GLM（国内推荐）=====
from langchain_community.chat_models import ChatZhipuAI
llm = ChatZhipuAI(model="glm-4", temperature=0.7)

# ===== 通用初始化方式 =====
from langchain.chat_models import init_chat_model
llm = init_chat_model("gpt-4o-mini")  # 自动识别提供商
```

#### 4.1.2 消息类型

LangChain 使用标准化的消息格式：

```python
from langchain_core.messages import (
    SystemMessage,    # 系统指令（设定角色和行为）
    HumanMessage,     # 用户消息
    AIMessage,        # AI 回复
)

# 方式一：直接传消息列表
messages = [
    SystemMessage(content="你是一个专业的翻译官，将中文翻译为英文"),
    HumanMessage(content="今天天气真好"),
]
response = llm.invoke(messages)
print(response.content)  # The weather is really nice today.

# 方式二：使用字符串（自动转为 HumanMessage）
response = llm.invoke("你好，介绍一下自己")
print(response.content)
```

#### 4.1.3 流式输出

```python
# 逐字输出，适合聊天场景
for chunk in llm.stream("给我讲一个故事"):
    print(chunk.content, end="", flush=True)
```

#### 4.1.4 批量处理

```python
# 同时处理多个请求
batch_responses = llm.batch([
    "翻译：hello",
    "翻译：world",
    "翻译：langchain",
])
for resp in batch_responses:
    print(resp.content)
```

### 4.2 LCEL：LangChain 表达式语言

**LCEL**（LangChain Expression Language）是 LangChain 的核心编排语法，使用 `|` 管道符将组件串联起来。

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# 创建提示词模板
prompt = ChatPromptTemplate.from_template("给我讲一个关于{topic}的{length}故事")

# 用 LCEL 串联：提示词 → 模型 → 输出解析
chain = prompt | llm | StrOutputParser()

# 执行
result = chain.invoke({"topic": "小猫", "length": "简短的"})
print(result)
```

**LCEL 的核心思想**：每个组件都实现 `Runnable` 接口，可以像管道一样组合：
- `invoke()` — 同步调用
- `stream()` — 流式调用
- `batch()` — 批量调用
- `ainvoke()` — 异步调用

### 4.3 Prompt 提示词工程

#### 4.3.1 ChatPromptTemplate

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 方式一：简单模板
prompt = ChatPromptTemplate.from_template(
    "你是一个{role}，请用{style}的语气回答以下问题：{question}"
)

# 方式二：多消息模板（推荐）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，回答要{style}"),
    ("human", "{question}"),
])

# 方式三：带历史消息的模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的助手"),
    MessagesPlaceholder("history"),  # 插入对话历史
    ("human", "{input}"),
])
```

#### 4.3.2 Message Prompt 变体

```python
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
)

system_template = SystemMessagePromptTemplate.from_template(
    "你是{company}的客服，请礼貌地回答客户问题"
)
human_template = HumanMessagePromptTemplate.from_template("{question}")
```

#### 4.3.3 Few-Shot 提示（少样本学习）

通过给模型几个示例来提升输出质量：

```python
from langchain_core.prompts import FewShotChatMessagePromptTemplate

# 定义示例
examples = [
    {"input": "开心", "output": "😊 你今天心情不错呀！"},
    {"input": "难过", "output": "😢 怎么了？跟我说说吧"},
    {"input": "生气", "output": "😤 深呼吸，冷静一下~"},
]

# 创建 few-shot 模板
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}"),
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

# 组合到完整提示中
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有同理心的助手，根据用户情绪给出温暖回应"),
    few_shot_prompt,
    ("human", "{input}"),
])

chain = final_prompt | llm | StrOutputParser()
print(chain.invoke({"input": "焦虑"}))
```

#### 4.3.4 OutputParser 输出解析器

让 AI 的输出变成结构化数据：

```python
from langchain_core.output_parsers import (
    StrOutputParser,      # 纯文本
    JsonOutputParser,     # JSON 格式
    CommaSeparatedListOutputParser,  # 逗号分隔列表
    PydanticOutputParser, # Pydantic 模型
)
from pydantic import BaseModel, Field

# === 方式一：JSON 输出 ===
json_parser = JsonOutputParser()
chain = prompt | llm | json_parser
result = chain.invoke({"question": "列出3种编程语言"})
# result: {"languages": ["Python", "JavaScript", "Go"]}

# === 方式二：Pydantic 模型 ===
class MovieReview(BaseModel):
    movie_name: str = Field(description="电影名称")
    rating: float = Field(description="评分，0-10")
    summary: str = Field(description="一句话总结")
    pros: list[str] = Field(description="优点列表")
    cons: list[str] = Field(description="缺点列表")

pydantic_parser = PydanticOutputParser(pydantic_object=MovieReview)

review_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个影评人。{format_instructions}"),
    ("human", "评价电影《流浪地球》"),
])

chain = review_prompt | llm | pydantic_parser
review = chain.invoke({
    "format_instructions": pydantic_parser.get_format_instructions()
})
print(review.movie_name)  # 流浪地球
print(review.rating)      # 8.5
```

---

## 五、阶段二：数据连接（Day 4-6）

RAG（检索增强生成）是 LangChain 最重要的应用场景之一。要实现 RAG，首先需要把文档变成 AI 能理解的格式。

### 5.1 Document Loaders 文档加载器

LangChain 支持加载各种格式的文档：

```python
# === 文本文件 ===
from langchain_community.document_loaders import TextLoader
loader = TextLoader("my_doc.txt", encoding="utf-8")
docs = loader.load()

# === PDF 文件 ===
from langchain_community.document_loaders import PyPDFLoader
loader = PyPDFLoader("report.pdf")
docs = loader.load()  # 每页一个 Document

# === Markdown 文件 ===
from langchain_community.document_loaders import UnstructuredMarkdownLoader
loader = UnstructuredMarkdownLoader("README.md")

# === 网页 ===
from langchain_community.document_loaders import WebBaseLoader
loader = WebBaseLoader("https://example.com/article")
docs = loader.load()

# === CSV 文件 ===
from langchain_community.document_loaders import CSVLoader
loader = CSVLoader("data.csv")

# === 目录批量加载 ===
from langchain_community.document_loaders import DirectoryLoader
loader = DirectoryLoader(
    "./docs",
    glob="**/*.md",     # 匹配模式
    loader_cls=TextLoader,
)
docs = loader.load()

# === Word 文档 ===
from langchain_community.document_loaders import Docx2txtLoader
loader = Docx2txtLoader("document.docx")
```

**Document 对象结构**：
```python
print(docs[0].page_content)  # 文本内容
print(docs[0].metadata)      # 元数据（来源文件、页码等）
```

### 5.2 Text Splitters 文本切分器

大文档需要切分成小块（chunk）才能有效检索：

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,  # 递归字符切分（推荐）
    CharacterTextSplitter,           # 字符切分
    MarkdownHeaderTextSplitter,      # Markdown 标题切分
    TokenTextSplitter,               # Token 切分
)

# === 推荐：递归字符切分 ===
# 按段落 → 句子 → 单词 的优先级递归切分
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每块最大 500 字符
    chunk_overlap=50,    # 块之间重叠 50 字符（保持上下文连贯）
    separators=["\n\n", "\n", "。", " ", ""],  # 切分优先级
)
chunks = splitter.split_documents(docs)
print(f"共 {len(chunks)} 个文本块")

# === Markdown 标题切分（保留标题层级）===
md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)
md_chunks = md_splitter.split_text("# 标题\n内容...")
```

**chunk_size 和 chunk_overlap 的选择建议**：

| 场景 | chunk_size | chunk_overlap | 说明 |
|------|-----------|--------------|------|
| 问答/FAQ | 200-300 | 50 | 短小精悍，精确匹配 |
| 文档摘要 | 500-1000 | 100 | 保留更多上下文 |
| 技术文档 | 800-1200 | 200 | 代码块需要完整性 |
| 长文分析 | 1000-2000 | 200 | 保留完整段落 |

### 5.3 Embeddings 向量嵌入

将文本转换为向量（数字数组），用于语义检索：

```python
# === OpenAI Embeddings ===
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# === 智谱 Embeddings（国内）===
from langchain_community.embeddings import ZhipuAIEmbeddings
embeddings = ZhipuAIEmbeddings(model="embedding-3")

# === HuggingFace 免费本地 Embeddings ===
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 使用示例
vector = embeddings.embed_query("这是一段测试文本")
print(f"向量维度: {len(vector)}")  # 通常 768 或 1536

# 批量向量化
vectors = embeddings.embed_documents(["文本1", "文本2", "文本3"])
```

**什么是 Embedding？**
> 把文本变成一串数字，语义相近的文本，数字也更接近。比如"猫"和"狗"的向量距离，比"猫"和"汽车"近得多。

### 5.4 Vector Stores 向量存储

将向量化的文本存储在数据库中，支持高效检索：

```python
from langchain_community.vectorstores import FAISS

# === 创建向量数据库 ===
vectorstore = FAISS.from_documents(
    documents=chunks,       # 文本块列表
    embedding=embeddings,   # Embedding 模型
)

# === 保存到本地 ===
vectorstore.save_local("my_faiss_index")

# === 从本地加载 ===
vectorstore = FAISS.load_local(
    "my_faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# === 添加新文档 ===
vectorstore.add_documents(new_chunks)

# === 合并两个向量库 ===
vectorstore.merge_from(other_vectorstore)
```

**其他向量数据库对比**：

| 数据库 | 类型 | 适用场景 |
|--------|------|----------|
| FAISS | 本地文件 | 开发测试、小规模数据 |
| Chroma | 本地/服务端 | 中等规模，开发友好 |
| Pinecone | 云服务 | 生产环境，大规模 |
| Milvus | 自托管 | 企业级，高性能 |
| Qdrant | 本地/云 | 平衡性能和易用性 |

### 5.5 Retrievers 检索器

从向量数据库中检索相关文档：

```python
# === 基础检索（相似度搜索）===
retriever = vectorstore.as_retriever(
    search_type="similarity",        # 相似度搜索
    search_kwargs={"k": 3},          # 返回最相似的 3 条
)
results = retriever.invoke("LangChain 怎么用？")
for doc in results:
    print(doc.page_content[:100], "...")

# === MMR 检索（最大边际相关性，结果更多样）===
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 10},  # 从10条中选最不重复的3条
)

# === 相似度阈值检索 ===
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8},  # 只返回相似度>0.8的结果
)
```

---

## 六、阶段三：RAG 检索增强生成（Day 7-9）

### 6.1 什么是 RAG？

**RAG（Retrieval-Augmented Generation，检索增强生成）** 的工作流程：

```
用户提问 → 检索相关文档 → 将文档+问题发给模型 → 模型基于文档回答
```

**为什么需要 RAG？**
- ❌ 直接问模型：模型可能编造答案（幻觉）
- ✅ RAG：模型基于真实文档回答，准确可靠

### 6.2 RAG 完整实现

```python
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ===== Step 1: 加载文档 =====
loader = DirectoryLoader("./my_docs", glob="**/*.txt", loader_cls=TextLoader)
docs = loader.load()
print(f"加载了 {len(docs)} 个文档")

# ===== Step 2: 切分文档 =====
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
chunks = splitter.split_documents(docs)
print(f"切分为 {len(chunks)} 个文本块")

# ===== Step 3: 向量化存储 =====
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("my_index")

# ===== Step 4: 创建检索器 =====
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ===== Step 5: 创建 RAG 链 =====
template = """根据以下上下文回答用户的问题。如果上下文中没有相关信息，请说"我不知道"。

上下文：
{context}

问题：{question}

回答："""

prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# ===== Step 6: 使用 =====
answer = rag_chain.invoke("LangChain 支持哪些模型？")
print(answer)
```

### 6.3 RAG 进阶技巧

#### 6.3.1 多路检索（Ensemble Retriever）

结合关键词检索和语义检索，提升召回率：

```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever

# BM25 关键词检索
bm25_retriever = BM25Retriever.from_documents(chunks, k=3)

# 向量语义检索
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 合并检索
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6],  # 语义检索权重更高
)
```

#### 6.3.2 对话式 RAG（带历史）

```python
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# 问题改写链：根据对话历史改写当前问题
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system", "根据对话历史，将最新问题改写为独立的问题"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_prompt
)

# 回答链
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "根据上下文回答问题"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# 使用
chat_history = []
question = "LangChain 是什么？"
response = rag_chain.invoke({"input": question, "history": chat_history})
chat_history.append(("human", question))
chat_history.append(("ai", response["answer"]))

# 后续问题可以引用上文
question2 = "它支持 Python 吗？"
response2 = rag_chain.invoke({"input": question2, "history": chat_history})
```

#### 6.3.3 Reranker 重排序

先粗检索多条，再用专门模型重排序取 top-k：

```python
# 需要安装: pip install langchain-cohere
from langchain_cohere import CohereRerank
from langchain_community.document_compressors import CohereRerank

compressor = CohereRerank(top_n=3)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=retriever
)
```

---

## 七、阶段四：Agent 智能体（Day 10-12）

### 7.1 什么是 Agent？

**Agent（智能体）** 是能自主思考并使用工具完成任务的 AI。

```
用户: "帮我查一下北京明天的天气，然后推荐适合的穿搭"

Agent 思考过程:
  1. 需要查天气 → 调用 weather_tool("北京")
  2. 获取结果: 晴，15-25°C → 调用 outfit_tool(晴, 15-25)
  3. 综合两个工具的结果，生成最终回答
```

### 7.2 Tools 工具定义

```python
from langchain.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# === 方式一：@tool 装饰器（推荐）===

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。输入必须是合法的 Python 数学表达式。"""
    try:
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_word_length(word: str) -> int:
    """返回一个单词的长度。"""
    return len(word)

# === 方式二：使用内置工具 ===

# 维基百科搜索
wiki_tool = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper()
)

# DuckDuckGo 搜索
from langchain_community.tools import DuckDuckGoSearchRun
search_tool = DuckDuckGoSearchRun()

# === 方式三：从函数创建 ===

def search_web(query: str) -> str:
    """搜索网页获取信息"""
    # 实现你的搜索逻辑
    return f"搜索结果: {query}"

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")

search_tool = StructuredTool.from_function(
    func=search_web,
    name="web_search",
    description="搜索互联网获取最新信息",
    args_schema=SearchInput,
)
```

**工具定义的关键**：
- `name`：工具名称，必须唯一
- `description`：**非常重要！** Agent 根据描述决定是否调用这个工具
- `args_schema`：参数的 schema，让 Agent 知道传什么参数

### 7.3 Agent 实现

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# 定义工具
@tool
def search_city_info(city: str) -> str:
    """查询城市的基本信息，包括人口、面积、特色等"""
    # 模拟数据库查询
    info_db = {
        "北京": "人口: 2189万, 面积: 16410km², 特色: 故宫、长城、烤鸭",
        "上海": "人口: 2487万, 面积: 6341km², 特色: 外滩、东方明珠、小笼包",
        "深圳": "人口: 1768万, 面积: 1997km², 特色: 科技之城、世界之窗、早茶",
    }
    return info_db.get(city, f"未找到 {city} 的信息")

@tool
def compare_cities(city1: str, city2: str) -> str:
    """比较两个城市的差异"""
    info1 = search_city_info(city1)
    info2 = search_city_info(city2)
    return f"{city1}: {info1}\n{city2}: {info2}"

# 创建 Agent
agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_city_info, compare_cities],
    system_prompt="""你是一个城市信息助手，可以查询和比较城市信息。
    回答要简洁有趣，适当使用emoji。""",
)

# 使用
result = agent.invoke({
    "messages": [{"role": "user", "content": "帮我比较北京和上海"}]
})
print(result["messages"][-1].content)
```

### 7.4 LangGraph 进阶

当 Agent 需要复杂的工作流（条件分支、循环、人工审批等），使用 LangGraph：

```python
# LangGraph 概念简介（暂不深入代码）
#
# StateGraph: 状态图，定义 Agent 的流程
# - Node: 一个处理步骤（调用模型、执行工具等）
# - Edge: 步骤之间的连接（普通边、条件边）
#
# 典型模式:
# 1. ReAct Agent: 思考 → 行动 → 观察 → 思考 → ... → 回答
# 2. Multi-Agent: 多个 Agent 协作完成复杂任务
# 3. Human-in-the-loop: 关键步骤需要人类确认
#
# 学习顺序建议:
# 先掌握 create_agent() → 再学 LangGraph 的 StateGraph
```

---

## 八、阶段五：Memory 记忆（Day 13-14）

让 AI 记住之前的对话内容：

```python
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
    SQLChatMessageHistory,  # SQLite 持久化
)
from langchain_core.runnables.history import RunnableWithMessageHistory

# === 内存记忆 ===
history = ChatMessageHistory()

# === SQLite 持久化记忆 ===
# pip install langchain-community
sql_history = SQLChatMessageHistory(
    session_id="user_001",
    connection_string="sqlite:///chat_history.db"
)

# === 给链添加记忆 ===
chain_with_memory = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,  # 获取对应 session 的历史
    input_messages_key="input",
    history_messages_key="history",
)

# 使用
config = {"configurable": {"session_id": "user_001"}}
response1 = chain_with_memory.invoke({"input": "我叫玖月"}, config=config)
response2 = chain_with_memory.invoke({"input": "我叫什么名字？"}, config=config)
# response2 应该能回答 "玖月"
```

---

## 九、实战项目

### 项目一：个人知识库问答助手（入门）

> **难度**：⭐⭐ | **时间**：2-3 天 | **学到**：文档加载、向量化、RAG

**功能**：
- 上传 TXT / MD / PDF 文档
- 自动切分 → 向量化 → 存储
- 对话式问答，支持上下文
- Web 界面（Gradio）

**项目结构**：
```
knowledge-base/
├── app.py              # Gradio Web 界面
├── config.py           # 配置文件
├── loader.py           # 文档加载和切分
├── vectorstore.py      # 向量存储管理
├── chain.py            # RAG 链构建
├── requirements.txt
└── docs/               # 存放上传的文档
```

**app.py 核心代码**：
```python
import gradio as gr
from chain import create_rag_chain
from vectorstore import VectorStoreManager
import os

# 初始化
config = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-4o-mini",
    "embedding_model": "text-embedding-3-small",
    "chunk_size": 500,
    "chunk_overlap": 50,
}

vs_manager = VectorStoreManager(config)

def upload_file(files):
    """处理上传的文件"""
    all_chunks = []
    for file in files:
        chunks = vs_manager.process_file(file.name)
        all_chunks.extend(chunks)
    vs_manager.save()
    return f"✅ 成功加载 {len(all_chunks)} 个文本块，知识库已更新！"

def chat(message, history):
    """对话"""
    if not vs_manager.is_ready():
        return "⚠️ 请先上传文档！"
    chain = create_rag_chain(vs_manager.get_retriever(), config)
    return chain.invoke({"input": message, "history": history})

# Gradio 界面
with gr.Blocks(title="个人知识库", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📚 个人知识库问答助手")
    
    with gr.Row():
        with gr.Column(scale=1):
            file_upload = gr.File(label="上传文档", file_types=[".txt", ".md", ".pdf"],
                                  file_count="multiple")
            upload_btn = gr.Button("处理文档", variant="primary")
            status = gr.Textbox(label="状态", interactive=False)
        
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=500)
            msg_input = gr.Textbox(label="提问", placeholder="输入你的问题...")
            send_btn = gr.Button("发送")
    
    upload_btn.click(upload_file, inputs=[file_upload], outputs=[status])
    send_btn.click(chat, inputs=[msg_input, chatbot], outputs=[chatbot])
    msg_input.submit(chat, inputs=[msg_input, chatbot], outputs=[chatbot])

demo.launch(server_name="0.0.0.0", server_port=7860)
```

---

### 项目二：AI 客服机器人（中级）

> **难度**：⭐⭐⭐ | **时间**：3-5 天 | **学到**：Agent、Tools、Memory、数据库集成

**功能**：
- 基于商品 FAQ 的 RAG 问答
- 查询订单状态的 Tool
- 查询物流信息的 Tool
- 推荐相关商品的 Tool
- 多轮对话记忆 + 用户信息记忆
- 简单的 Web 聊天界面

**项目结构**：
```
ai-customer-service/
├── app.py              # FastAPI + Web 界面
├── models.py           # 数据模型
├── database.py         # SQLite 数据库操作
├── tools.py            # 自定义工具
├── agent.py            # Agent 构建
├── faq_loader.py       # FAQ 加载
├── requirements.txt
└── data/
    ├── faq.json        # FAQ 数据
    ├── products.json   # 商品数据
    └── orders.db       # 订单数据库
```

**tools.py 核心代码**：
```python
from langchain.tools import tool
from database import Database

db = Database()

@tool
def query_order(order_id: str) -> str:
    """查询订单状态。输入订单号，返回订单的当前状态和详细信息。"""
    order = db.get_order(order_id)
    if not order:
        return f"未找到订单号 {order_id}，请检查订单号是否正确。"
    return (f"📦 订单 {order_id}\n"
            f"商品: {order['product_name']}\n"
            f"金额: ¥{order['amount']}\n"
            f"状态: {order['status']}\n"
            f"物流: {order['logistics']}")

@tool
def query_logistics(order_id: str) -> str:
    """查询物流信息。输入订单号，返回物流跟踪信息。"""
    logistics = db.get_logistics(order_id)
    if not logistics:
        return f"未找到订单 {order_id} 的物流信息。"
    return "\n".join(f"📍 {step['time']}: {step['desc']}" for step in logistics)

@tool
def recommend_product(category: str, budget: float = None) -> str:
    """推荐商品。输入品类名称和可选预算，返回推荐商品列表。"""
    products = db.get_products_by_category(category, budget)
    if not products:
        return f"没有找到 {category} 品类的商品。"
    result = "🛍️ 为您推荐以下商品：\n"
    for p in products:
        result += f"- {p['name']}: ¥{p['price']}, {p['desc']}\n"
    return result

@tool
def process_return(order_id: str, reason: str) -> str:
    """提交退货申请。输入订单号和退货原因，提交退货申请。"""
    success = db.create_return_request(order_id, reason)
    if success:
        return f"✅ 退货申请已提交！订单 {order_id}，原因：{reason}。预计 1-3 个工作日处理。"
    return f"❌ 退货申请失败，请联系人工客服。"
```

---

### 项目三：自动研究报告生成器（高级）

> **难度**：⭐⭐⭐⭐ | **时间**：5-7 天 | **学到**：LangGraph、多步 Agent、搜索工具、文档生成

**功能**：
- 输入研究主题
- AI 自动拆解为子主题
- 搜索收集资料（多轮搜索）
- 对每个子主题生成摘要
- 合并生成完整报告（Markdown + PDF）
- 支持人

工作流

**流程图**：
```
用户输入主题
    ↓
AI 拆解为 3-5 个子主题
    ↓
对每个子主题:
    → 搜索收集资料
    → 筛选有价值的信息
    → 生成子主题摘要
    ↓
合并所有子主题摘要
    ↓
生成完整报告结构
    ↓
输出 Markdown / PDF
```

**项目结构**：
```
research-report/
├── app.py                  # 主程序（命令行 / Web）
├── agents/
│   ├── planner.py          # 主题拆解 Agent
│   ├── researcher.py       # 资料搜索 Agent
│   ├── writer.py           # 报告撰写 Agent
│   └── reviewer.py         # 质量审核 Agent
├── tools/
│   ├── web_search.py       # 搜索工具
│   ├── url_reader.py       # 网页内容提取
│   └── file_writer.py      # 文件写入工具
├── utils/
│   ├── prompts.py          # 提示词模板
│   └── formatters.py       # 输出格式化
├── requirements.txt
└── output/                 # 生成的报告
```

**planner.py 核心代码**：
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class ResearchPlan(BaseModel):
    title: str = Field(description="报告标题")
    subtopics: list[str] = Field(description="子主题列表")
    outline: str = Field(description="报告大纲")

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
parser = JsonOutputParser(pydantic_object=ResearchPlan)

prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的研究助手。用户会给你一个研究主题，你需要：
    1. 将主题拆解为 3-5 个子主题
    2. 为每个子主题确定研究要点
    3. 生成报告大纲
    
    {format_instructions}"""),
    ("human", "研究主题：{topic}"),
])

planner_chain = prompt | llm | parser

plan = planner_chain.invoke({
    "topic": "2025年新能源汽车市场趋势",
    "format_instructions": parser.get_format_instructions(),
})
print(plan)
# 输出示例:
# title: "2025年新能源汽车市场趋势研究报告"
# subtopics: ["市场规模分析", "技术发展动态", "政策环境", "竞争格局"]
# outline: "1. 概述 2. 市场规模..."
```

**researcher.py 核心代码**：
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

@tool
def search_web(query: str) -> str:
    """搜索互联网获取最新信息"""
    # 实际使用时接入真实搜索 API
    import requests
    # ... 搜索逻辑
    return results

@tool
def read_webpage(url: str) -> str:
    """读取网页内容"""
    import requests
    from bs4 import BeautifulSoup
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    return soup.get_text()[:3000]

researcher_agent = create_agent(
    model="gpt-4o",
    tools=[search_web, read_webpage],
    system_prompt="""你是一个专业的研究员。对于每个子主题：
    1. 搜索 3-5 个相关信息源
    2. 提取关键数据和观点
    3. 写一段 200-300 字的摘要
    
    摘要要包含：数据来源、关键数字、主要结论。
    如果信息不足，明确标注 [需要更多研究]。
    """,
)

# 对每个子主题执行研究
for subtopic in plan["subtopics"]:
    result = researcher_agent.invoke({
        "messages": [{"role": "user", "content": f"研究子主题：{subtopic}"}]
    })
    # 保存研究结果...
```

---

## 十、参考资源

### 官方资源
- 📖 **LangChain 官方文档**：https://python.langchain.com/docs/
- 📖 **LangGraph 文档**：https://langchain-ai.github.io/langgraph/
- 🧪 **LangSmith 追踪平台**：https://smith.langchain.com/
- 💻 **GitHub 仓库**：https://github.com/langchain-ai/langchain
- 📚 **LangChain Hub（模板库）**：https://smith.langchain.com/hub

### 中文学习资源
- 📺 **B站**：搜索 "LangChain 教程"，有多个从入门到实战的系列
- 📝 **掘金**：搜索 "LangChain学习与实战" 系列（作者 Qborfy，循序渐进）
- 📝 **博客园**：搜索 "LangChain 入门"、"LangChain RAG" 等关键词
- 📝 **知乎**：搜索 "LangChain 完整指南"、"万字长文 LangChain"

### 推荐阅读顺序
1. **Day 1-3**：跑通本文档第四章的所有代码示例
2. **Day 4-6**：理解数据连接，自己切分文档、建向量库
3. **Day 7-9**：做一个能读文档回答问题的 RAG demo
4. **Day 10-12**：学习 Agent，让 AI 调用工具完成任务
5. **Day 13-14**：添加 Memory，做对话式应用
6. **Day 15+**：选择一个实战项目，从零搭建完整应用

### 视频课程推荐
- B站搜 "LangChain大模型全套教程"（七天入门到就业）
- B站搜 "LangChain实战"（项目驱动）

---

> 💡 **学习建议**：
> 1. **先跑通再理解**：不要一上来就看理论，先把代码跑起来
> 2. **多改多试**：改改参数、换换模型，看看效果有什么变化
> 3. **做项目学最快**：从项目一（知识库问答）开始，边做边学
> 4. **善用 LangSmith**：调试 Agent 时用 LangSmith 看调用链路
> 5. **关注官方更新**：LangChain 更新很快，多看官方 changelog
