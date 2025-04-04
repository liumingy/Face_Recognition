import cv2
import matplotlib
from matplotlib import pyplot as plt


def draw_rectangle(image, left_up, right_down, save_path="test.jpg"):
    matplotlib.use('Agg')
    # 创建绘图
    fig, ax = plt.subplots()
    ax.imshow(image)

    # 计算矩形参数
    x, y = left_up
    width = right_down[0] - left_up[0]
    height = right_down[1] - left_up[1]

    # 绘制矩形框
    rect = plt.Rectangle((x, y), width, height, linewidth=2, edgecolor='r', facecolor='none')
    ax.add_patch(rect)

    # 去掉坐标轴
    plt.axis('off')

    # 保存图像
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close()

def draw_point(image, point, save_path="test.jpg"):
    cv2.circle(image, point, 5, (0, 0, 255), -1)  # 画红色实心圆，半径 5
    cv2.imwrite(save_path, cv2.cvtColor(image, cv2.COLOR_BGR2RGB))