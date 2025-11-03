import os, torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from tqdm import tqdm
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt

# ============================================================
# 1. ACON-C Activation
# ============================================================
class ACONC(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.p1 = nn.Parameter(torch.ones(1, width, 1, 1))
        self.p2 = nn.Parameter(torch.zeros(1, width, 1, 1))
        self.beta = nn.Parameter(torch.ones(1, width, 1, 1))
    def forward(self, x):
        return (self.p1 - self.p2) * x * torch.sigmoid(self.beta * x) + self.p2 * x


# ============================================================
# 2. Fractional Gabor Filter (FGF)
# ============================================================
class FGF2D(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=15):
        super().__init__()
        self.theta = nn.Parameter(torch.rand(out_channels) * np.pi)
        self.scale = nn.Parameter(torch.ones(out_channels))
        self.freq = nn.Parameter(torch.ones(out_channels) * 0.25)
        self.kernel_size = kernel_size
        self.in_channels = in_channels
        self.out_channels = out_channels

    def forward(self, x):
        ks = self.kernel_size
        device = x.device
        grid = torch.linspace(-1, 1, ks, device=device)
        X, Y = torch.meshgrid(grid, grid, indexing="ij")
        kernels = []
        for i in range(self.out_channels):
            θ, s, f = self.theta[i], self.scale[i], self.freq[i]
            xθ = X * torch.cos(θ) + Y * torch.sin(θ)
            yθ = -X * torch.sin(θ) + Y * torch.cos(θ)
            g = torch.exp(-(xθ**2 + (yθ/s)**2)) * torch.cos(2 * np.pi * f * xθ)
            kernels.append(g)
        kernel = torch.stack(kernels).unsqueeze(1)  # [out,1,ks,ks]
        return F.conv2d(x, kernel.repeat(1, self.in_channels, 1, 1), padding=ks//2)


# ============================================================
# 3. Model: FGF + ACON-C CNN
# ============================================================
class FGF_ACON_Model(nn.Module):
    def __init__(self, num_classes=12):
        super().__init__()
        self.fgf = FGF2D(1, 16, kernel_size=15)
        self.block1 = nn.Sequential(
            nn.Conv2d(16, 32, 3, padding=1),
            ACONC(32),
            nn.MaxPool2d(2))
        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1),
            ACONC(64),
            nn.MaxPool2d(2))
        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1),
            ACONC(128),
            nn.AdaptiveAvgPool2d(1))
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.fgf(x)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        return self.fc(x.view(x.size(0), -1))


# ============================================================
# 4. Training and Evaluation
# ============================================================
def train_model(model, train_dl, test_dl, epochs=20, lr=1e-3, device='cuda'):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    model.to(device)

    for epoch in range(epochs):
        model.train()
        total, correct, loss_sum = 0, 0, 0
        for xb, yb in tqdm(train_dl, desc=f"Epoch {epoch+1}/{epochs}"):
            xb, yb = xb.to(device), yb.to(device)
            out = model(xb)
            loss = loss_fn(out, yb)
            opt.zero_grad(); loss.backward(); opt.step()
            loss_sum += loss.item() * xb.size(0)
            correct += (out.argmax(1) == yb).sum().item()
            total += xb.size(0)
        acc = correct / total
        print(f"Train Loss: {loss_sum/total:.4f}, Acc: {acc:.4f}")

        evaluate(model, test_dl, device)

def evaluate(model, test_dl, device='cuda'):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for xb, yb in test_dl:
            xb, yb = xb.to(device), yb.to(device)
            out = model(xb)
            y_pred.extend(out.argmax(1).cpu().numpy())
            y_true.extend(yb.cpu().numpy())
    acc = np.mean(np.array(y_true) == np.array(y_pred))
    print(f"✅ Test Acc: {acc:.4f}")
    return acc


# ============================================================
# 5. Dataset & Training Loop
# ============================================================
if __name__ == "__main__":
    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    train_ds = datasets.ImageFolder("c03-racom/train", transform=transform)
    test_ds  = datasets.ImageFolder("c03-racom/test",  transform=transform)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=2)
    test_dl  = DataLoader(test_ds,  batch_size=32, shuffle=False, num_workers=2)

    print(f"🧩 Classes: {train_ds.classes}")

    model = FGF_ACON_Model(num_classes=len(train_ds.classes))
    train_model(model, train_dl, test_dl, epochs=30, lr=1e-3)
