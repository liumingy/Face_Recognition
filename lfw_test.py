import torch
import torch.backends.cudnn as cudnn
import os
import numpy as np

from nets.facenet import Facenet
from utils.dataloader import LFWDataset
from utils.utils_metrics import test

def count_parameters(model):
    """
    计算模型的参数量
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def calculate_model_size(model_path):
    """
    计算模型文件大小（MB）
    """
    size_bytes = os.path.getsize(model_path)
    size_mb = size_bytes / (1024 * 1024)
    return size_mb

if __name__ == "__main__":
    #--------------------------------------#
    #   是否使用Cuda
    #   没有GPU可以设置成False
    #--------------------------------------#
    cuda            = False
    #--------------------------------------#
    #   主干特征提取网络的选择
    #   mobilenet
    #   inception_resnetv1
    #--------------------------------------#
    backbone        = "inception_resnetv1"
    #--------------------------------------------------------#
    #   输入图像大小，常用设置如[112, 112, 3]
    #--------------------------------------------------------#
    input_shape     = [160, 160, 3]
    #--------------------------------------#
    #   训练好的权值文件
    #--------------------------------------#
    model_path      = "model/facenet_inception_resnetv1.pth"
    #--------------------------------------#
    #   LFW评估数据集的文件路径
    #   以及对应的txt文件
    #--------------------------------------#
    lfw_dir_path    = "lfw_test"
    lfw_pairs_path  = "lfw_test/pairs.txt"
    #--------------------------------------#
    #   评估的批次大小和记录间隔
    #--------------------------------------#
    batch_size      = 256
    log_interval    = 1
    #--------------------------------------#
    #   ROC图的保存路径
    #--------------------------------------#
    png_save_path   = "roc_test.png"

    # 计算模型文件大小
    model_size = calculate_model_size(model_path)
    print(f"模型大小: {model_size:.2f} MB")

    test_loader = torch.utils.data.DataLoader(
        LFWDataset(dir=lfw_dir_path, pairs_path=lfw_pairs_path, image_size=input_shape), batch_size=batch_size, shuffle=False)

    model = Facenet(backbone=backbone, mode="predict")

    # 计算模型参数量
    params_count = count_parameters(model)
    print(f"模型参数量: {params_count:,}")

    print('Loading weights into state dict...')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.load_state_dict(torch.load(model_path, map_location=device), strict=False)
    model  = model.eval()

    if cuda:
        model = torch.nn.DataParallel(model)
        cudnn.benchmark = True
        model = model.cuda()

    test(test_loader, model, png_save_path, log_interval, batch_size, cuda)
