from pyecharts import options as opts
from pyecharts.charts import Bar

# 创建柱形图对象
bar = Bar()

# 添加 X 轴数据
bar.add_xaxis(["Category 1", "Category 2", "Category 3"])

# 添加数据系列
data = [100, 200, 300]
bar.add_yaxis("Series 1", data)

# 设置视觉映射
bar.set_global_opts(
    visualmap_opts=opts.VisualMapOpts(
        min_=min(data),
        max_=max(data),
        range_color=["#FF7F50", "#32CD32"],
    )
)

# 渲染图表
bar.render("bar_chart.html")
