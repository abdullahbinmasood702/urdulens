**350 lines, dataset: all**

| Engine | Lines | CER | WER | Exact lines | Speed |
|---|---|---|---|---|---|
| easyocr | 350 | 13.6% | 49.2% | 9.4% | 546 ms |
| tesseract | 350 | 39.2% | 57.2% | 32.6% | 49 ms |

**CER by style**

| Engine | nastaliq | naskh |
|---|---|---|
| easyocr | 21.0% | 8.7% |
| tesseract | 49.5% | 32.3% |

**CER by degradation**

| Engine | clean | mild | heavy |
|---|---|---|---|
| easyocr | 10.5% | 14.8% | 14.9% |
| tesseract | 15.7% | 31.8% | 73.7% |
