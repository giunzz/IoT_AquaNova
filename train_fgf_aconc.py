import os, torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from tqdm import tqdm
import numpy as np
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
        self.freq  = nn.Parameter(torch.ones(out_channels) * 0.25)
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
        kernel = torch.stack(kernels).unsqueeze(1)
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
def evaluate(model, loader, device='cuda'):
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            out = model(xb)
            correct += (out.argmax(1) == yb).sum().item()
            total += xb.size(0)
    return correct / total


def train_model(model, train_dl, test_dl, epochs=30, lr=1e-3, device='cuda', resume=False):
    output_dir = "/kaggle/working"
    ckpt_dir = os.path.join(output_dir, "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)

    log_file = open(os.path.join(output_dir, "train_log.txt"), "a")

    # 🔧 Khởi tạo optimizer + loss function
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    best_acc, start_epoch = 0, 0
    model.to(device)

    # Resume checkpoint nếu có
    if resume and os.path.exists(os.path.join(ckpt_dir, "last.pth")):
        ckpt = torch.load(os.path.join(ckpt_dir, "last.pth"), map_location=device)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["optimizer"])
        start_epoch = ckpt["epoch"] + 1
        best_acc = ckpt["best_acc"]
        print(f"🔄 Resumed from epoch {start_epoch}, best acc={best_acc:.2f}")

    for epoch in range(start_epoch, epochs):
        model.train()
        total_loss, correct, total = 0, 0, 0
        pbar = tqdm(train_dl, desc=f"🧭 Epoch {epoch+1}/{epochs}", colour="cyan")

        for xb, yb in pbar:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            out = model(xb)
            loss = loss_fn(out, yb)
            loss.backward()
            opt.step()

            total_loss += loss.item() * xb.size(0)
            correct += (out.argmax(1) == yb).sum().item()
            total += xb.size(0)

            pbar.set_postfix({
                "loss": f"{total_loss/total:.4f}",
                "acc": f"{(correct/total)*100:.2f}%",
                "lr": f"{opt.param_groups[0]['lr']:.1e}"
            })

        # Validation
        val_acc = evaluate(model, test_dl, device)
        train_acc = correct / total
        print(f"✅ Epoch {epoch+1} | Train Acc: {train_acc*100:.2f}% | Val Acc: {val_acc*100:.2f}%")

        log_file.write(f"{epoch+1},{train_acc:.4f},{val_acc:.4f}\n")
        log_file.flush()

        # Save checkpoints
        torch.save({
            "epoch": epoch,
            "model": model.state_dict(),
            "optimizer": opt.state_dict(),
            "best_acc": best_acc
        }, os.path.join(ckpt_dir, "last.pth"))

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), os.path.join(ckpt_dir, "best_model.pth"))
            print(f"💾 New best model saved at epoch {epoch+1} (Val Acc {val_acc*100:.2f}%)")

    log_file.close()
    print(f"🎯 Training completed. Best Val Acc = {best_acc*100:.2f}%")

    # =====================================================
    # 📦 Lưu các parameter FGF (theta, scale, freq)
    # =====================================================
    theta = model.fgf.theta.detach().cpu().numpy()
    scale = model.fgf.scale.detach().cpu().numpy()
    freq = model.fgf.freq.detach().cpu().numpy()

    param_path = os.path.join(output_dir, "fgf_parameters.csv")
    with open(param_path, "w") as f:
        f.write("Filter,Theta(deg),Scale,Freq\n")
        for i in range(len(theta)):
            f.write(f"{i},{np.degrees(theta[i]):.3f},{scale[i]:.4f},{freq[i]:.4f}\n")

    print(f"📑 Saved FGF parameters to: {param_path}")


# ============================================================
# 5. Dataset & Training Loop
# ============================================================
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"

    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    # === Dataset path ===
    data_root = "/kaggle/input/c03-racom"
    train_ds = datasets.ImageFolder(os.path.join(data_root, "train"), transform=transform)
    test_ds  = datasets.ImageFolder(os.path.join(data_root, "test"),  transform=transform)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=2)
    test_dl  = DataLoader(test_ds,  batch_size=32, shuffle=False, num_workers=2)

    print(f"🧩 Classes: {train_ds.classes}")

    model = FGF_ACON_Model(num_classes=len(train_ds.classes))
    train_model(model, train_dl, test_dl, epochs=30, lr=1e-3, device=device)
