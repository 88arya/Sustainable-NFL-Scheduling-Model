The NFL leads all major U.S. sports leagues in terms of carbon footprint per game, primarily due to team travel. This project uses a Binary Integer Programming (BIP) model to generate an NFL season schedule that is most carbon-efficient with respect to travel.

Results:

![Emissions Comparison](results/emissions_comparison_bar_metric_tonnes.png)

### Raw Data

<details>
<summary>Click to expand</summary>

| year | actual_value | optimal_value | percent_decrease |
|------|--------------|---------------|-----------------|
| 2021 | 10421.56134  | 9793.19559    | 6.03            |
| 2022 | 9290.35811   | 8823.58170    | 5.02            |
| 2023 | 10572.54057  | 10036.19230   | 5.07            |
| 2024 | 10409.79270  | 9845.80495    | 5.42            |
| 2025 | 10294.43774  | 9706.57613    | 5.71            |

</details>

### How it works

Each season's matchups are determined on a rotating basis and by the in-division rank of the previous season for every team. **Playwright** was used to scrape the official NFL website to determine seasonal matchups.

An integer program was formulated in **PuLP** and solved with **CBC**. This was done for years 2021–2025. The optimal NFL schedule for each year can be found in:

```text
model/output/<year>/<year>_schedule.csv
