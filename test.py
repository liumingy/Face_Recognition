import torch
import tensorflow as tf
import numpy as np
import os
from add_history import AddHistory
from camera import register, Compare
path = r"D:\PythonWorkspace\Face_Recognition\model\20180408-102900\20180408-102900.pb"

def count_tf_model_parameters(pb_file_path):
    """
    统计TensorFlow .pb模型文件的参数量
    
    参数:
        pb_file_path: pb文件路径
        
    返回:
        参数总量
    """
    print(f"加载模型: {pb_file_path}")
    
    # 获取模型大小（MB）
    size_bytes = os.path.getsize(pb_file_path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"模型文件大小: {size_mb:.2f} MB")
    
    # 创建图
    with tf.Graph().as_default() as graph:
        # 加载模型
        with tf.gfile.GFile(pb_file_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            tf.import_graph_def(graph_def, name='')
        
        # 获取图中所有操作
        ops = graph.get_operations()
        
        # 统计操作类型
        op_types = {}
        for op in ops:
            op_type = op.type
            if op_type in op_types:
                op_types[op_type] += 1
            else:
                op_types[op_type] = 1
        
        print(f"\n模型中操作类型数量: {len(op_types)}")
        
        # 统计常量操作中的参数数量
        total_parameters = 0
        for op in ops:
            # 主要查找卷积、全连接等层的权重常量
            if op.type == 'Const':
                # 获取常量的值
                try:
                    with tf.Session() as sess:
                        tensor = op.outputs[0]
                        # 只考虑权重张量（通常是多维的）
                        if len(tensor.shape) > 1:  
                            tensor_value = sess.run(tensor)
                            # 计算张量中的元素数量
                            num_params = np.prod(tensor_value.shape)
                            if num_params > 100:  # 过滤掉一些小常量
                                print(f"常量 {op.name}: 形状 {tensor_value.shape}, 参数数量: {num_params:,}")
                                total_parameters += num_params
                except Exception as e:
                    continue
        
        # 使用另一种方法尝试获取参数数量
        if total_parameters == 0:
            print("\n使用替代方法估算参数量...")
            for op in ops:
                if 'weight' in op.name.lower() or 'kernel' in op.name.lower() or 'filter' in op.name.lower():
                    try:
                        with tf.Session() as sess:
                            tensor = op.outputs[0]
                            tensor_shape = tensor.shape.as_list()
                            if all(dim is not None for dim in tensor_shape):
                                num_params = np.prod(tensor_shape)
                                print(f"权重 {op.name}: 形状 {tensor_shape}, 参数数量: {num_params:,}")
                                total_parameters += num_params
                    except Exception as e:
                        continue
        
        print(f"\n估计总参数量: {total_parameters:,}")
        return total_parameters, size_mb

# 统计模型参数量
if __name__ == "__main__":
    params, size = count_tf_model_parameters(path)
    print("\n===================总结===================")
    print(f"模型: InceptionResNetV1")
    print(f"文件大小: {size:.2f} MB")
    print(f"参数量: {params:,}")

# # 创建比较神经网络
# compare = Compare()
# # 运行线程
# compare.start()
# register(202112135, "刘明宇", 1, 1)




