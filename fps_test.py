import cv2
import numpy as np
import tensorflow as tf
from align import detect_face
import time
from facenet import Facenet
from PIL import Image
import threading

def test_mtcnn_fps():
    # mtcnn相关参数
    minsize = 40
    threshold = [0.6, 0.7, 0.7]  # pnet、rnet、onet三个网络输出人脸的阈值
    factor = 0.709  # scale factor
    margin = 40
    image_size = 160
    
    # 创建mtcnn网络
    with tf.Graph().as_default():
        sess = tf.Session()
        with sess.as_default():
            pnet, rnet, onet = detect_face.create_mtcnn(sess, './align/')
    
    # 获取一张测试图像
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头，将使用随机图像")
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    else:
        ret, frame = cap.read()
        if ret:
            test_image = frame
        else:
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cap.release()
    
    # 转换为RGB格式
    rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
    
    # 测试参数
    warmup_runs = 100  # 预热次数
    total_runs = 500  # 总运行次数 = 预热 + 测试
    detect_times = []
    
    print(f"\n开始MTCNN测试，共{total_runs}次运行，前{warmup_runs}次为预热...")
    start_time = time.time()
    
    # 运行测试，包括预热和正式测试
    for i in range(total_runs):
        start_detect = time.time()
        bounding_boxes, _ = detect_face.detect_face(rgb_image, minsize, pnet, rnet, onet, threshold, factor)
        detect_time = time.time() - start_detect
        detect_times.append(detect_time)
        
        # 显示进度
        if (i+1) % 50 == 0:
            current_phase = "预热" if i < warmup_runs else "测试"
            print(f"进度: {i+1}/{total_runs} ({current_phase}), 当前检测耗时: {detect_time*1000:.2f}ms")
    
    # 只统计预热后的数据
    test_times = detect_times[warmup_runs:]
    test_start_time = start_time + sum(detect_times[:warmup_runs])
    test_total_time = sum(test_times)
    
    # 计算统计信息
    avg_detect_time = sum(test_times) / len(test_times)
    avg_fps = 1.0 / avg_detect_time
    
    # 打印最终统计信息
    print(f"\n测试结果 (忽略前{warmup_runs}次预热):")
    print(f"有效测试次数: {len(test_times)}")
    print(f"总时间: {test_total_time:.2f}秒")
    print(f"平均检测时间: {avg_detect_time*1000:.2f}ms")
    print(f"最小检测时间: {min(test_times)*1000:.2f}ms")
    print(f"最大检测时间: {max(test_times)*1000:.2f}ms")
    print(f"平均FPS: {avg_fps:.2f}")
    
    # 打印检测到的人脸数量
    if len(bounding_boxes) > 0:
        print(f"检测到{len(bounding_boxes)}个人脸")
    else:
        print("未检测到人脸")

def test_facenet_fps():
    # MTCNN相关参数
    minsize = 40
    threshold = [0.6, 0.7, 0.7]
    factor = 0.709
    margin = 44
    image_size = 160
    
    # 创建mtcnn网络
    with tf.Graph().as_default():
        sess = tf.Session()
        with sess.as_default():
            pnet, rnet, onet = detect_face.create_mtcnn(sess, './align/')
    
    # 加载Facenet模型
    model = Facenet()
    
    # 尝试打开摄像头获取一张图像，并使用MTCNN进行预处理
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头，将使用随机图像")
        test_image = np.random.randint(0, 255, (image_size, image_size, 3), dtype=np.uint8)
        pil_image = Image.fromarray(test_image)
    else:
        ret, frame = cap.read()
        if ret:
            print("使用MTCNN进行人脸预处理...")
            # 使用MTCNN检测人脸
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bounding_boxes, _ = detect_face.detect_face(rgb_frame, minsize, pnet, rnet, onet, threshold, factor)
            
            if len(bounding_boxes) > 0:
                # 获取第一个检测到的人脸
                det = np.squeeze(bounding_boxes[0, 0:4])
                bb = np.zeros(4, dtype=np.int32)
                bb[0] = np.maximum(det[0] - margin / 2, 0)
                bb[1] = np.maximum(det[1] - margin / 2, 0)
                bb[2] = np.minimum(det[2] + margin / 2, rgb_frame.shape[1])
                bb[3] = np.minimum(det[3] + margin / 2, rgb_frame.shape[0])
                
                # 裁剪人脸区域
                cropped = rgb_frame[bb[1]:bb[3], bb[0]:bb[2], :]
                aligned = cv2.resize(cropped, (image_size, image_size))
                cv2.imwrite("detected_face.jpg", cv2.cvtColor(aligned, cv2.COLOR_RGB2BGR))
                print(f"已检测到人脸并保存为detected_face.jpg")
                pil_image = Image.fromarray(aligned)
            else:
                print("未检测到人脸，将使用中心区域")
                # 裁剪中心区域并调整大小
                h, w = frame.shape[:2]
                min_dim = min(h, w)
                top = (h - min_dim) // 2
                left = (w - min_dim) // 2
                cropped = frame[top:top+min_dim, left:left+min_dim]
                test_image = cv2.resize(cropped, (image_size, image_size))
                test_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(test_image)
        else:
            test_image = np.random.randint(0, 255, (image_size, image_size, 3), dtype=np.uint8)
            pil_image = Image.fromarray(test_image)
        cap.release()
    
    # 初始化变量
    warmup_runs = 100  # 预热次数
    total_runs = 500  # 总运行次数 = 预热 + 测试
    embed_times = []
    
    print(f"\n开始Facenet测试，共{total_runs}次运行，前{warmup_runs}次为预热...")
    
    # 运行测试，包括预热和正式测试
    for i in range(total_runs):
        start_embed = time.time()
        emb = np.array(model.detect_image(pil_image), dtype=np.float32)
        embed_time = time.time() - start_embed
        embed_times.append(embed_time)
        
        # 显示进度
        if (i+1) % 50 == 0:
            current_phase = "预热" if i < warmup_runs else "测试"
            print(f"进度: {i+1}/{total_runs} ({current_phase}), 当前特征提取耗时: {embed_time*1000:.2f}ms")
    
    # 只统计预热后的数据
    test_times = embed_times[warmup_runs:]
    test_total_time = sum(test_times)
    
    # 计算统计信息
    avg_embed_time = sum(test_times) / len(test_times)
    avg_fps = 1.0 / avg_embed_time
    
    # 打印结果
    print(f"\n测试结果 (忽略前{warmup_runs}次预热):")
    print(f"有效测试次数: {len(test_times)}")
    print(f"总时间: {test_total_time:.2f}秒")
    print(f"平均特征提取时间: {avg_embed_time*1000:.2f}ms")
    print(f"最小特征提取时间: {min(test_times)*1000:.2f}ms")
    print(f"最大特征提取时间: {max(test_times)*1000:.2f}ms")
    print(f"平均FPS: {avg_fps:.2f}")
    print(f"特征向量维度: {emb.shape[0]}")
    print("\n注意: 此测试仅包括Facenet特征提取时间，不包括MTCNN检测时间")

if __name__ == "__main__":
    # 选择要测试的功能
    print("请选择要测试的功能：")
    print("1. 测试MTCNN帧率") # 23
    print("2. 测试Facenet帧率") # 1 15
    choice = input("请输入选项（1或2）：")
    
    if choice == "1":
        test_mtcnn_fps()
    elif choice == "2":
        test_facenet_fps()
    else:
        print("无效的选项")