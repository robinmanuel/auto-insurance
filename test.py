import torch

ckpt = torch.load("models/parts_segmentation.pt", map_location="cpu")
print(type(ckpt))