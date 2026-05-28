# data

此資料夾放置可重複使用的資料處理工具與產生出的特徵表。

- `loader.py`：讀取城市軌跡 CSV，並切分 train / validation / test 資料。
- `preprocessing.py`：平假日標記、網格熱力圖、網格座標與經緯度轉換。
- `grid_to_latlon.csv`：已追蹤的 200x200 網格對照表，用於 POI 對齊。

產生檔案：

- `grid_clusters.csv`：由 `analysis.clustering.run_hdbscan` 產生。
- `user_hotspots.csv`：由 `analysis.clustering.assign_user_hotspots` 產生。
- `grid_poi_features.csv`：由 `analysis.clustering.build_grid_poi_features` 產生。
- `user_stability_features.csv`：由 `analysis.trajectory.build_user_stability_features` 產生。

大型原始 CSV 請放在 `raw_data/`，該資料夾已被 Git 忽略。
