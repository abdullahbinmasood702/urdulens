**350 lines, dataset: all**

| Engine | Lines | CER | WER | Exact lines | Speed |
|---|---|---|---|---|---|
| easyocr | 350 | 13.6% | 49.1% | 8.9% | 2041 ms |
| tesseract | 350 | 45.9% | 61.2% | 30.3% | 187 ms |

**CER by style**

| Engine | nastaliq | naskh |
|---|---|---|
| easyocr | 20.7% | 8.8% |
| tesseract | 56.7% | 38.7% |

**CER by degradation**

| Engine | clean | mild | heavy |
|---|---|---|---|
| easyocr | 10.6% | 14.9% | 14.7% |
| tesseract | 23.9% | 36.5% | 82.1% |
