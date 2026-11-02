# FormoSync E4B

**理解臺灣繁體中文，讓工具操作回到對話脈絡。**

[English](README.md) · [完整評測](docs/evaluation.md) · [資料版本](docs/data.md) · [授權與來源](NOTICE.md)

FormoSync E4B 是針對臺灣華語工作對話與 TeamSync 工具使用微調的文字 LoRA adapter。目標是把「理解使用者在說什麼」和「下一步應如何操作」接起來：讀懂上下文、確認資料結構、選擇工具，並只使用已知資訊填入參數。

名稱結合 **Formosa** 與 **Sync**；完整版本名稱為 **FormoSync-Nemotron-E4B-zhTW-Tool-v0.1**。

本版對應 **Round 6、step 768**。它在部分自建工具與繁中測試有改善，也在其他工具、停止呼叫及知識測試出現退步。完整自動驗收條件尚未通過，因此以研究用途呈現這份成果。

## 我們想改善的問題

工作對話常會省略主詞、指向前文，或在一句話中改口，例如「剛才那筆，數量不是三個，改兩個」。工具操作需要同時理解這些語意，並確認目前有哪些表格、欄位與紀錄可用。

本專案著重三件事：

- **依結構操作資料：**查找表格與欄位、辨認紀錄、使用正確型別，從伺服器實際提供的工具中選擇讀取、準備或執行動作。
- **結合前文理解臺灣華語：**處理省略、指涉、改口、日期、數量與語氣，不要求使用者先改寫成正式命令。
- **分清楚語句與授權：**「可以」可能是確認剛顯示的提案，也可能只是表示聽懂欄位說明；是否能執行仍由上下文與伺服器能力決定。

這些是訓練目標，不代表模型已能可靠處理所有模糊表達。

## 模型身分

| 項目 | 內容 |
|---|---|
| 發布形式 | 完整 PEFT LoRA adapter，另需原始 base model |
| Base model | [`nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16) |
| 固定 revision | `49843eed8db1f1c616c47af75cfd36e07aec0667` |
| 上游基礎 | NVIDIA model card 所述的 Google Gemma 4 E4B-it |
| 初始化 | 從固定 base 建立新的 LoRA |
| 選定 checkpoint | Round 6 step768 |
| LoRA rank／alpha | 16／32 |
| 訓練設定 | NF4 4-bit base、BF16 計算、learning rate `1e-5`、有效 batch 8 |
| 訓練進度 | 7,000 筆資料跑一個 875-update epoch，依開發集選擇 step768 |
| 訓練模態 | 文字與工具呼叫對話 |

Adapter 大小為 139,602,808 bytes，SHA-256 為：

```text
fecf928856466c605aed86cc55d23e9fdb8da7f8c7fb06a381c140c2da53bd05
```

儲存後曾以新的 base 重新載入，並核對所有 adapter tensor。`E4B` 沿用上游命名，不應直接當成總參數量或顯存需求的承諾。

## 新跑完整比較 — 2026-11-02

兩個固定模型都已完成測試，題目 ID、runtime 版本與評測協定一致。TMMLU+ 使用 zero-shot 選項字母似然法，與官方 few-shot 排行榜協定不同。

| 指標 | NVIDIA base | FormoSync E4B |
|---|---:|---:|
| TMMLU+／完整測試 | 10049/19680 (51.06%) | 9743/19680 (49.51%) |
| TMMLU+／67 科平均 | 51.53% | 49.99% |
| 固定 Custom Table 測試 | 25/40 (62.50%) | 24/40 (60.00%) |
| 固定 TeamSync 情境 | 94/114 (82.46%) | 109/114 (95.61%) |
| 固定一般工具情境 | 25/30 (83.33%) | 24/30 (80.00%) |
| 固定繁中理解 | 28/40 (70.00%) | 32/40 (80.00%) |
| 語用理解 | 0/28 (0.00%) | 9/28 (32.14%) |
| 語用工具操作 | 13/28 (46.43%) | 16/28 (57.14%) |
| 聯合 Custom Table 測試 | 13/32 (40.62%) | 31/32 (96.88%) |
| 固定測試／避免多餘呼叫 | 100.00% | 82.00% |
| 語用測試／避免多餘呼叫 | 100.00% | 66.67% |
| 聯合 CT／避免多餘呼叫 | 100.00% | 100.00% |

[結果與驗證附件](https://github.com/ShuChenAI/formosync/releases/tag/benchmark-20261102) · [完整 JSON](docs/benchmark-20261102-results.json)。工具情境測試與訓練共用規則，且曾作診斷使用；這些結果不代表完整語言能力或正式部署驗收。

完整 TMMLU+ 的正確率下降約 **1.55 個百分點**，少答對 306 題；工具與部分繁中情境有改善，但另有指標退步，不能概括為全面優於 base。

## 原始 R6 封存評測

下表保留原始 R6 封存結果，與上方新跑的完整測試分開呈現。

以下來自儲存後模型的評測，不是訓練 loss 或開發集調參分數。

| 測試 | Base | FormoSync E4B |
|---|---:|---:|
| 自建聯合 Custom Table 測試 | 13/32 | **31/32** |
| 固定 TeamSync 情境 | 94/114 | **109/114** |
| 固定繁中理解測試 | 28/40 | **32/40** |
| 臺灣華語語用理解 | 0/28 | **9/28** |
| 臺灣華語語用工具操作 | 13/28 | **16/28** |
| 固定 Custom Table 測試 | **25/40** | 24/40 |
| 固定一般工具情境 | **25/30** | 24/30 |
| 保留知識測試 | **336/670（50.15%）** | 319/670（47.61%） |

在應避免多餘工具呼叫的指標上，固定測試由 100% 降至 82%，語用測試由 100% 降至 66.67%；聯合 CT 測試則維持 100%。自建評測沒有記錄到未授權提交嘗試，但測試未執行真實後端寫入，不能據此宣稱實際部署已通過安全驗收。

自建測試與訓練情境共用部分規則，且沒有獨立人工評測。31/32 的結果也不能概括為所有 Custom Table 操作都優於 base；另一組固定 CT 測試就少通過一題。完整數字、截斷情況與失敗條件見[評測說明](docs/evaluation.md)及[原始彙總結果](docs/evaluation-results.json)。

## 本版實際使用的資料

| 類型 | 筆數 | 比例 |
|---|---:|---:|
| TeamSync 工具操作 | 2,800 | 40% |
| 公開臺灣繁中對話 | 2,450 | 35% |
| 有明確依據的語意理解 | 1,050 | 15% |
| 權限、歧義與確認的成對邊界情境 | 700 | 10% |
| **合計** | **7,000** | **100%** |

每筆資料的初始權重都是 1.0。700 筆邊界資料組成 350 對，包含 400 筆合理工具呼叫與 300 筆不呼叫工具的目標。壓縮訓練檔 SHA-256 為：

```text
9eaaef69d7b827c8996f5b565289b6def000b0c800d11dda1a32007373722d09
```

TeamSync 與語意情境是助手撰寫的虛構世界及工具回覆。公開繁中資料來自經篩選的 TWLLM 對話，回答由其他語言模型替換產生，並未逐筆人工驗證。**本 adapter 未使用私人 LangSmith 客戶對話訓練。**格式及個資樣式過濾也不等於完整匿名化或事實正確性認證。

後續另準備了 10,000 筆、50% 工具／40% 自然繁中／10% 語意理解的資料，但該輪沒有完成任何 optimizer update，**不能把它寫成本版模型已學過的資料**。兩個版本的組成、雜湊與取樣方式分別記錄在[資料說明](docs/data.md)。

## 下載與載入

權重、tokenizer 與資料包放在 [GitHub Releases](https://github.com/ShuChenAI/formosync/releases/tag/v0.1.0)。完整下載、安裝與 CLI 指令見 [English README](README.md#download-and-run)。

原始參考環境為 Python 3.12.16、PyTorch 2.7.1+cu118、Transformers 5.21.0、PEFT 0.21.2、bitsandbytes 0.50.2，使用 H100 MIG 40GB。這是已記錄的環境，不代表最低硬體需求，亦未在其他環境重新認證。

先取得固定 revision 的完整 NVIDIA base，放入 `models/base/`，保留設定、tokenizer、索引與 `model-frozen-shared-kv.safetensors`。再將發布包中的 adapter 與相符的 tokenizer／template 放入 `models/adapter/`。

```bash
hf download nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16 \
  --revision 49843eed8db1f1c616c47af75cfd36e07aec0667 \
  --local-dir models/base
```

完整載入與生成程式見 [English README](README.md#loading-the-adapter)。該範例依照原始 model class 與量化設定整理，尚未在保留的參考環境以外重新跑 GPU smoke test。

工具使用時，將當前工具 JSON schema 傳入原生 chat template 的 `tools` 參數，並依上游格式解析工具呼叫。本 adapter 不包含後端連線或工具執行器。

## 應用程式仍需負責的邊界

權限、資料範圍、參數驗證、確認與實際執行都由應用程式負責：

- `requires_confirmation_for_ct_action` 是伺服器政策，不是模型可產生的工具參數。
- 只有伺服器確認目前提案已 armed，才提供對應的執行能力；token 取自當前伺服器提供的描述。
- 是否完成寫入，以工具實際成功的回覆為依據，不能只相信模型說「已完成」。

由於部分 no-call 指標退步，接上可寫入工具前，應用自己的 schema 與停止／澄清情境重新評估。

## 適用範圍與限制

目前沒有對廣泛臺灣語言能力、臺語或語碼混用的獨立人工驗證，也沒有證明微調改善了圖片或音訊能力。知識測試的退步、公開 teacher 回答可能錯誤，以及完整驗收未通過，都是本版應保留的結果。

## 授權與貢獻

本專案程式與新撰文件採 [Apache-2.0](LICENSE)。模型材料保留 [OpenMDW-1.1](licenses/OpenMDW-1.1.txt) 及上游來源聲明；資料依各組成來源的授權與 attribution 處理。詳見 [NOTICE.md](NOTICE.md)。

歡迎提供獨立撰寫的繁中測試、確認與歧義對照案例、schema grounding 檢查及可重現的執行報告。回報結果時請附 base revision、adapter SHA、template 與 decoding 設定，並避免在公開 issue／PR 中放入客戶對話、憑證或私人業務資料。
