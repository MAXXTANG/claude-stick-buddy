# Claude Stick Buddy — Behance 作品集草稿

Repository: https://github.com/MAXXTANG/claude-stick-buddy

## 專案標題

Claude Stick Buddy｜實體 AI 工具核准裝置｜Firmware / BLE / Interaction Design

## 短描述

一台放在桌上的 M5StickS3，透過 Claude Desktop 的 Hardware Buddy BLE 協定接收權限提示，顯示工具資訊、用量狀態與像素吉祥物，並讓使用者用實體按鍵核准或拒絕工具呼叫。

## 角色

Firmware design、Embedded UI、BLE protocol integration、Python local bridge、Mascot animation system、Documentation。

## 技術堆疊

- M5Stack M5StickS3 / ESP32-S3
- PlatformIO + Arduino-ESP32
- M5Unified / NimBLE-Arduino / ArduinoJson / AnimatedGIF
- Python + bleak
- macOS launchd

## 5 頁簡報圖片

### 01. Cover

File: `docs/behance-01-cover.png`

Caption:
Claude Stick Buddy is a pocket hardware companion for Claude Desktop, turning permission prompts into a physical desk interaction.

### 02. Project Context

File: `docs/behance-02-context.png`

Caption:
工具核准不該只停在螢幕裡。這個專案把 Claude Desktop 的 permission moment 轉成可看見、可觸摸、可快速 glance 的硬體互動。

### 03. Interaction Flow

File: `docs/behance-03-interaction.png`

Caption:
Claude Desktop sends a prompt over BLE. The stick wakes, shows the tool name and hint, then waits for a physical button decision.

### 04. System Architecture

File: `docs/behance-04-architecture.png`

Caption:
系統分成 Claude Desktop BLE heartbeat、M5StickS3 firmware、以及本機 usage bridge。重連 panic 的修正重點是讓 NimBLE callback 只收資料，所有 parsing/UI/speaker work 都回到 main loop 執行。

### 05. Mascot And Deliverables

File: `docs/behance-05-mascot.png`

Caption:
吉祥物動畫由 Python script 產生 embedded GIF data，包含 idle、heart、bulb、dizzy 等狀態，讓裝置在 idle 時仍保有生命感。

## 建議 Behance 排版

1. 直接上傳 5 張 1600×900 圖，按檔名順序排列。
2. 圖與圖之間保持白底或黑底留白，不要再加長段說明，讓圖片自己說明專案。
3. 作品描述欄放「短描述、角色、技術堆疊、Repository」即可。
4. Tags 可用：Firmware Design、ESP32、BLE、Hardware Prototype、Interaction Design、Claude Desktop、Open Source。

## Credits

Forked from `p3ob7o/hwbuddy-notifier-S3`, based on Anthropic's Hardware Buddy BLE protocol. GPL-3.0-or-later.
