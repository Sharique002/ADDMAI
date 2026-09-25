"""MesoNet-4 inspired Convolutional Neural Network architecture (Stage 3).

Conforms to Sections 5 & 6 of Stage 3 specifications.
Provides compact, reproducible, locally executable deepfake artifact classification.
"""

import torch
import torch.nn as nn


class ADDMAIDeepfakeDetector(nn.Module):
    """MesoNet-4 inspired CNN for facial/image manipulation artifact detection.

    Input: Normalized image tensor of shape (B, 3, 224, 224)
    Output: Raw classification logit of shape (B, 1)
    """

    def __init__(self) -> None:
        super().__init__()
        # Conv Block 1
        self.conv1 = nn.Conv2d(3, 8, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(8)
        self.relu1 = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Conv Block 2
        self.conv2 = nn.Conv2d(8, 8, kernel_size=5, padding=2, bias=False)
        self.bn2 = nn.BatchNorm2d(8)
        self.relu2 = nn.ReLU(inplace=True)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Conv Block 3
        self.conv3 = nn.Conv2d(8, 16, kernel_size=5, padding=2, bias=False)
        self.bn3 = nn.BatchNorm2d(16)
        self.relu3 = nn.ReLU(inplace=True)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Conv Block 4
        self.conv4 = nn.Conv2d(16, 16, kernel_size=5, padding=2, bias=False)
        self.bn4 = nn.BatchNorm2d(16)
        self.relu4 = nn.ReLU(inplace=True)
        self.pool4 = nn.MaxPool2d(kernel_size=4, stride=4)

        # Classification Head: 224 -> pool1(112) -> pool2(56) -> pool3(28) -> pool4(7)
        # 16 * 7 * 7 = 784
        self.flatten = nn.Flatten()
        self.dropout = nn.Dropout(0.5)
        self.fc1 = nn.Linear(16 * 7 * 7, 16)
        self.leaky_relu = nn.LeakyReLU(0.1)
        self.dropout2 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(16, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through feature extractor and binary classification head."""
        x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x = self.pool3(self.relu3(self.bn3(self.conv3(x))))
        x = self.pool4(self.relu4(self.bn4(self.conv4(x))))
        x = self.flatten(x)
        x = self.dropout(x)
        x = self.leaky_relu(self.fc1(x))
        x = self.dropout2(x)
        x = self.fc2(x)
        return x
