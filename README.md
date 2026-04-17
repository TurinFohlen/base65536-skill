# Base65536-Skill

> 将任意文件编码为纯文本，安全绕过平台文件格式限制，防监听窃密。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 解决的问题

很多 AI 平台（如 MiniMax、ChatGPT 等）的网页界面**不支持上传二进制文件**，只允许粘贴纯文本。

本工具可以将**任意格式的文件**（ZIP、图片、视频、PDF、EXE……）编码为一段可打印的 Unicode 文本，直接粘贴到聊天框中传输。

配合加密模式，还能防止传输过程中的窃密和监听。

---

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 📦 **任意格式** | 支持所有文件类型：二进制、图片、音视频、压缩包、可执行文件等 |
| 🔤 **纯文本传输** | 编码后仅为 Unicode 文本，粘贴到任意文本框即可 |
| 🗜️ **gzip 压缩** | 文本类文件压缩率 70-80%，总体积减少显著 |
| 🔐 **XOR 加密模式** | SHA-256 密钥 + 字节级异或加密，密文无元数据泄漏 |
| 🛡️ **防监听** | 传输内容为不可读的 Unicode，TLS 层面也无法识别文件类型 |
| 📄 **元数据隐藏** | 加密模式下文件名、大小均为假数据，密钥丢失无法恢复 |

---

## 📖 使用方法

### 安装依赖

```bash
pip install base65536
```

### 基本用法

```bash
# 编码（无加密）
python skill.py encode document.pdf -o encoded.txt

# 解码
python skill.py decode encoded.txt -o restored.pdf
```

### 加密模式（防止窃密）

```bash
# 加密编码
python skill.py encode secret.zip --scramble -o encrypted.txt
# 输出示例：
#   🔑 密钥（整数）: 108544482569932551567348223456789012...
#   ✓ 已编码: encrypted.txt

# 解密还原（必须提供密钥）
python skill.py decode encrypted.txt --key 108544482569932551567348223456789012...
```

---

## 🔒 安全说明

### 加密模式下的保护

加密模式下，传输的文本**完全隐藏**以下信息：

- ✅ 原始文件名（显示为 `encrypted_file`）
- ✅ 原始文件大小（显示为 `0`）
- ✅ 文件真实类型（二进制乱码）
- ✅ 文件内容（XOR 加密，无密钥无法还原）

### 防监听原理

```
明文文件 → gzip压缩 → Base65536编码 → XOR加密(可选) → Unicode文本
```

1. **Base65536 编码**：将二进制转换为 Unicode 特殊字符，TLS 加密层无法识别为文件
2. **XOR 加密**：使用 SHA-256 密钥生成伪随机密钥流，字节级异或加密，只有知道密钥才能解密
3. **元数据伪造**：即使被截获，文件头显示为 `encrypted_file`，大小为 0

### 注意事项

- ⚠️ **密钥必须妥善保管**，丢失后无法恢复
- ⚠️ 加密模式下密钥以明文输出，请通过安全渠道传递（如分开传递、端到端加密通讯等）
- ⚠️ 本工具主要用于保护传输安全，本地文件安全请使用系统级加密（BitLocker、FileVault 等）

---

## 📊 压缩效率

| 文件类型 | 原始大小 | Base65536后 | 压缩率 |
|---------|---------|------------|--------|
| 纯文本 (.txt) | 10 KB | ~4 KB | ~40% |
| Python源码 (.py) | 50 KB | ~20 KB | ~40% |
| ZIP压缩包 (.zip) | 8 KB | ~8 KB | ~100% (已压缩) |
| 图片 (.jpg) | 200 KB | ~100 KB | ~50% |
| PDF文档 (.pdf) | 500 KB | ~260 KB | ~52% |

> Base65536 每字符表示 2 字节，理论膨胀率 ~50%。启用 gzip 后文本类文件压缩率 70-80%，综合效率优秀。

---

## 📁 文件格式

编码后文本文件结构：

```
#METADATA:{"original_name": "原始文件名", "compressed": true, "original_size": 12345, "scrambled": false}
[Base65536编码数据...]
```

加密模式下：

```
#METADATA:{"original_name": "encrypted_file", "compressed": true, "original_size": 0, "scrambled": true, "note": "..."}
[XOR加密后的Base65536编码数据...]
###ENCRYPTED_META###[加密的元数据（真实文件名、大小）]
```

---

## 🚀 应用场景

1. **平台文件上传限制**：在不支持文件上传的 AI 平台传输文件
2. **隐私保护**：在不信任的渠道传输敏感文件（配合加密模式）
3. **隐写术结合**：将文件编码为文本后可嵌入图片、代码注释等载体
4. **API 传输**：在纯文本 API 中传输二进制数据
5. **跨平台数据迁移**：不受文件格式兼容性限制

---

## 📂 文件结构

```
base65536-skill/
├── README.md                      # 本文件
├── SKILL.md                      # OpenClaw Skill 元数据
├── requirements.txt              # Python 依赖
├── scripts/
│   └── skill.py                # 主程序（编码/解码/加密）
└── references/
    └── encoding-details.md       # 编码原理详解
```

---

## 🤖 OpenClaw Skill 集成

本项目已打包为 OpenClaw Skill，可直接在 OpenClaw 中使用：

```bash
# 安装到 OpenClaw
openclaw skills install base65536-skill

# 使用
openclaw skill run base65536 encode yourfile.zip -o encoded.txt
openclaw skill run base65536 decode encoded.txt --key 密钥
```

---

## 📜 许可证

MIT License - 可自由使用、修改、分发。
