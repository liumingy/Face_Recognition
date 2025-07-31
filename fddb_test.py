import cv2
import tensorflow as tf
import matplotlib.pyplot as plt
from align import detect_face
import os

def main():
    # MTCNN相关参数
    minsize = 40  # 最小脸部尺寸
    threshold = [0.6, 0.7, 0.7]  # pnet、rnet、onet的置信度阈值
    factor = 0.709  # 图像金字塔的缩放因子
    
    # 创建MTCNN网络
    print("正在加载MTCNN模型...")
    with tf.Graph().as_default():
        sess = tf.Session()
        with sess.as_default():
            pnet, rnet, onet = detect_face.create_mtcnn(sess, './align/')
            
            # 要处理的图像文件列表
            image_files = ["FDDB_1.jpg", "FDDB_2.jpg", "FDDB_3.jpg", "FDDB_4.jpg"]
            
            # 创建保存结果的目录
            output_dir = "fddb_results"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 处理每张图像
            for img_file in image_files:
                print(f"处理图像: {img_file}")
                
                # 读取图像
                img = cv2.imread(img_file)
                if img is None:
                    print(f"无法读取图像 {img_file}")
                    continue
                
                # 转换为RGB（MTCNN的输入）
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # 使用MTCNN检测人脸
                bounding_boxes, points = detect_face.detect_face(img_rgb, minsize, pnet, rnet, onet, threshold, factor)
                
                # 创建结果图像的副本
                result_img = img.copy()
                
                # 在图像上标记检测到的人脸
                face_count = len(bounding_boxes)
                print(f"检测到 {face_count} 个人脸")
                
                # 在图像上绘制人脸框和关键点
                for i in range(face_count):
                    # 获取人脸框坐标
                    box = bounding_boxes[i]
                    x1, y1, x2, y2, _ = box
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # 绘制人脸框 (绿色)
                    cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # 绘制5个关键点 (红色)
                    for j in range(5):
                        cv2.circle(result_img, (int(points[j][i]), int(points[j+5][i])), 3, (0, 0, 255), -1)
                
                # 保存结果图像
                output_path = os.path.join(output_dir, f"detected_{img_file}")
                cv2.imwrite(output_path, result_img)
                print(f"结果已保存至: {output_path}")

if __name__ == "__main__":
    main()
