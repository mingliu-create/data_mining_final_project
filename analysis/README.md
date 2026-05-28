# analysis

此資料夾放置特徵工程與探索性分析模組。

- `eda.py`：空間熱力圖、軌跡密度、每日活躍使用者等視覺化工具。
- `clustering.py`：網格密度、HDBSCAN/DBSCAN 熱點分群、使用者熱點標記、POI 特徵建立。
- `trajectory.py`：使用者移動穩定性特徵，包含重複率、熵值與移動類型。

分析後可重複使用的特徵應輸出到 `data/`；圖表輸出到 `output/figures/`。
